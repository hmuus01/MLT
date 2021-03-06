import torch
import torch.nn as nn
import torch.nn.functional as F


class SegnetOpencv(nn.Module):
    """Class for the segnet network witht the canny filter."""
    def __init__(self):
        super().__init__()

        self.layer_10 = self.conv2d_layer(3, 64)
        self.layer_11 = self.conv2d_layer(64, 64)

        self.layer_20 = self.conv2d_layer(64, 128)
        self.layer_21 = self.conv2d_layer(128, 128)

        self.layer_30 = self.conv2d_layer(128, 256)
        self.layer_31 = self.conv2d_layer(256, 256)
        self.layer_32 = self.conv2d_layer(256, 256)

        self.layer_40 = self.conv2d_layer(256, 512)
        self.layer_41 = self.conv2d_layer(512, 512)
        self.layer_42 = self.conv2d_layer(512, 512)

        self.layer_50 = self.conv2d_layer(512, 512)
        self.layer_51 = self.conv2d_layer(512, 512)
        self.layer_52 = self.conv2d_layer(512, 512)

        self.downsample = nn.MaxPool2d(2, stride=2, return_indices=True)

        self.layer_52_t = self.conv2d_layer(512, 512)
        self.layer_51_t = self.conv2d_layer(512, 512)
        self.layer_50_t = self.conv2d_layer(512, 512)

        self.layer_42_t = self.conv2d_layer(512, 512)
        self.layer_41_t = self.conv2d_layer(512, 512)
        self.layer_40_t = self.conv2d_layer(512, 256)

        self.layer_32_t = self.conv2d_layer(256, 256)
        self.layer_31_t = self.conv2d_layer(256, 256)
        self.layer_30_t = self.conv2d_layer(256, 128)

        self.layer_21_t = self.conv2d_layer(128, 128)
        self.layer_20_t = self.conv2d_layer(128, 64)

        self.layer_11_t = self.conv2d_layer(64, 64)
        self.layer_10_t = self.conv2d_layer(64, 2)

        self.filter_layer_1 = self.conv2d_layer(64, 64)
        self.filter_layer_2 = self.conv2d_layer(64, 1)

        self.upsample = nn.MaxUnpool2d(2, stride=2)

        self.linear_c_0 = nn.Linear(512 * 8 * 8, 128)
        self.linear_c_1 = nn.Linear(128, 2)

        self.linear_b_0 = nn.Linear(512 * 8 * 8, 64)
        self.linear_b_1 = nn.Linear(64, 4)

        self.flat = nn.Flatten()

    def vgg16_init(self, vgg16):
        """A function for vgg weights of the pretrained model.
        
        Args:
        vgg16: model.
        """

        original_layers = [self.layer_10, self.layer_11, self.layer_20, self.layer_21
            , self.layer_30, self.layer_31, self.layer_32
            , self.layer_40, self.layer_41, self.layer_42
            , self.layer_50, self.layer_51, self.layer_52]

        layers = list(vgg16.features.children())  # Getting all features of vgg

        vgg_layers = []
        for layer in layers:
            if isinstance(layer, nn.Conv2d):
                vgg_layers.append(layer)

        SegnetEnc = []

        for layer in original_layers:

            for l in layer:  # loop through sequential
                if isinstance(l, nn.Conv2d):
                    SegnetEnc.append(l)

        assert len(vgg_layers) == len(SegnetEnc)

        for layer1, layer2 in zip(vgg_layers, SegnetEnc):
            layer2.weight.data = layer1.weight.data
            layer2.bias.data = layer1.bias.data

    def conv2d_layer(self, in_ch, out_ch, kernel_size=3, padding=1, stride=1):
        """A function creating a layer consisting of batch normalisation convolution and relu.
        Args:
            in_ch (int): Number of input channels.
            out_ch (int): Number of output channels.
            kernel_size (int): size of the kernel for the convolution. Default is 3.
            padding (int, optional): Padding for the convolution stage. Default is 1.
            Stride (int): Stride for the convolution layer. Default is 1.
        
        Returns:
            A structure made up of three smaller layers.
        
        """
        layer = []
        layer.append(nn.BatchNorm2d(in_ch))
        layer.append(
            nn.Conv2d(in_channels=in_ch, out_channels=out_ch, kernel_size=kernel_size, padding=padding, stride=stride))
        layer.append(nn.ReLU(inplace=True))

        return nn.Sequential(*layer)

    def forward(self, x):

        # Encoder
        x = self.layer_10(x)
        x = self.layer_11(x)
        x, i1 = self.downsample(x)
        x1 = x.size()

        # print(x.shape)

        x = self.layer_20(x)
        x = self.layer_21(x)
        x, i2 = self.downsample(x)
        x2 = x.size()

        # print(x.shape)

        x = self.layer_30(x)
        x = self.layer_31(x)
        x = self.layer_32(x)
        x, i3 = self.downsample(x)
        x3 = x.size()

        # print(x.shape)

        x = self.layer_40(x)
        x = self.layer_41(x)
        x = self.layer_42(x)
        x, i4 = self.downsample(x)
        x4 = x.size()

        # print(x.shape)

        x = self.layer_50(x)
        x = self.layer_51(x)
        x = self.layer_52(x)
        x, i5 = self.downsample(x)
        x5 = x.size()

        # Find image embedding
        flat = self.flat(x)
        # print(flat.size(),"flatsize")

        ########################
        # Compute MLT branches
        ########################

        # Classification task.
        c_0 = F.relu(self.linear_c_0(flat))
        c_ = (self.linear_c_1(c_0))

        # Bounding Boxes task
        b_0 = F.relu(self.linear_b_0(flat))
        b_ = F.relu(self.linear_b_1(b_0))

        # print(x.shape)

        x = self.upsample(x, i5, output_size=x4)
        x = self.layer_52_t(x)
        x = self.layer_51_t(x)
        x = self.layer_50_t(x)

        # print(x.shape)

        x = self.upsample(x, i4, output_size=x3)
        x = self.layer_42_t(x)
        x = self.layer_41_t(x)
        x = self.layer_40_t(x)

        # print(x.shape)

        x = self.upsample(x, i3, output_size=x2)
        x = self.layer_32_t(x)
        x = self.layer_31_t(x)
        x = self.layer_30_t(x)

        # print(x.shape)

        x = self.upsample(x, i2, output_size=x1)
        x = self.layer_21_t(x)
        x = self.layer_20_t(x)
        # print(x.shape)

        x = self.upsample(x, i1)

        filter_layer_1 = self.filter_layer_1(x)
        filter_layer_2 = self.filter_layer_2(filter_layer_1)

        x = self.layer_11_t(x)
        x = self.layer_10_t(x)

        # print(x.shape)

        return c_, b_, x, filter_layer_2


class AttentionBlock(nn.Module):

    def __init__(self, in_channel, inter_channel, out_channel, features, in_channel_3, out_channel_3):
        """
        @params:
        features: Shared features (From the 3rd or so conv) to be multiplied element-wise
        in_channel: Number of in_channels for 1st 1x1 conv
        inter_channel: Intermediate channels for 2nd 1x1 conv
        out_channels: Out channels for 2nd 1x1 conv
        in_channel_3: In channels for 3x3 conv
        out_channel_3: Out channels for 3x3 conv
        """

        super().__init__()

        self.attention_weights = self.attention(in_channel, inter_channel, out_channel)
        self.features = features
        self.conv_layer = self.conv2d_layer(in_channel_3, out_channel_3)

    def conv2d_layer(self, in_ch, out_ch, kernel_size=3, padding=1, stride=1):
        """A function creating a layer consisting of batch normalisation convolution and relu.
        Args:
            in_ch (int): Number of input channels.
            out_ch (int): Number of output channels.
            kernel_size (int): size of the kernel for the convolution. Default is 3.
            padding (int, optional): Padding for the convolution stage. Default is 1.
            Stride (int): Stride for the convolution layer. Default is 1.
        
        Returns:
            A structure made up of three smaller layers.
        
        """
        layer = []
        layer.append(nn.BatchNorm2d(in_ch))
        layer.append(
            nn.Conv2d(in_channels=in_ch, out_channels=out_ch, kernel_size=kernel_size, padding=padding, stride=stride))
        layer.append(nn.ReLU(inplace=True))
        return nn.Sequential(*layer)

    def attention_(self, in_channel, inter_channel, out_channel):
        """A function for the attention consisting of 2 convolutions, batch normalization, relu and sigmoid layers.
        Args:
            in_channel (int): Number of input channels.
            inter_channel (int): Number of inter channels.
            out_channel (int): Number of output channels.
            
        Returns:
            A structure consisting of 6 individual smaller layers.
            
        """
        layer = []

        layer.append(nn.Conv2d(in_channels=in_channel, out_channels=out_channel, kernel_size=1, padding=0))
        layer.append(nn.BatchNorm2d(inter_channel))
        layer.append(nn.ReLU(inplace=True))
        layer.append(nn.Conv2d(in_channels=in_channel, out_channels=inter_channel, kernel_size=1, padding=0))
        layer.append(nn.BatchNorm2d(out_channel))
        layer.append(nn.Sigmoid())

        return nn.Sequential(*layer)

    def forward(self, x):
        x = self.attention_weights(x)
        x = x * self.features
        x = self.conv_layer(x)
        return x
