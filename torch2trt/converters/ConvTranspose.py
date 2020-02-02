from torch2trt.torch2trt import *
from torch2trt.module_test import add_module_test


@tensorrt_converter('torch.nn.ConvTranspose2d.forward')
@tensorrt_converter('torch.nn.ConvTranspose3d.forward')
def convert_ConvTranspose2d(ctx):
    module = ctx.method_args[0]
    input = ctx.method_args[1]
    input_trt = trt_(ctx.network, input)
    output = ctx.method_return

    input_dim = input.dim() - 2

    kernel_size = module.kernel_size
    if not isinstance(kernel_size, tuple):
        kernel_size = (kernel_size, ) * input_dim

    stride = module.stride
    if not isinstance(stride, tuple):
        stride = (stride, ) * input_dim

    padding = module.padding
    if not isinstance(padding, tuple):
        padding = (padding, ) * input_dim

    assert module.dilation == 1 or all([d == 1 for d in module.dilation]), \
        "Transposed convolution dilation is not supported in TensorRT"       

    kernel = module.weight.detach().cpu().numpy()
    
    bias = trt.Weights(torch_dtype_to_trt(module.weight.dtype))
    if module.bias is not None:
        bias = module.bias.detach().cpu().numpy()

    layer = ctx.network.add_deconvolution_nd(
        input=input_trt,
        num_output_maps=module.out_channels,
        kernel_shape=kernel_size,
        kernel=kernel,
        bias=bias)
    layer.stride_nd = stride
    layer.padding_nd = padding
    
    if module.groups is not None:
        layer.num_groups = module.groups

    output._trt = layer.get_output(0)


@add_module_test(torch.float32, torch.device('cuda'), [(1, 10, 7, 7)])
def test_ConvTranspose2d_basic():
    return torch.nn.ConvTranspose2d(10, 5, kernel_size=1, stride=1, padding=0)


@add_module_test(torch.float32, torch.device('cuda'), [(1, 10, 8, 8)])
def test_ConvTranspose2d_stride2():
    return torch.nn.ConvTranspose2d(10, 5, kernel_size=1, stride=2, padding=0)

@add_module_test(torch.float32, torch.device('cuda'), [(1, 10, 9, 9)])
def test_ConvTranspose2d_kernel3():
    return torch.nn.ConvTranspose2d(10, 5, kernel_size=3, stride=2, padding=1)



@add_module_test(torch.float32, torch.device('cuda'), [(1, 10, 7, 7, 7)])
def test_ConvTranspose3d_basic():
    return torch.nn.ConvTranspose3d(10, 5, kernel_size=1, stride=1, padding=0)


@add_module_test(torch.float32, torch.device('cuda'), [(1, 10, 7, 7, 7)])
def test_ConvTranspose3d_stride2():
    return torch.nn.ConvTranspose3d(10, 5, kernel_size=1, stride=2, padding=0)


@add_module_test(torch.float32, torch.device('cuda'), [(1, 10, 6, 6, 6)])
def test_ConvTranspose3d_kernel3():
    return torch.nn.ConvTranspose3d(10, 5, kernel_size=3, stride=2, padding=1)

