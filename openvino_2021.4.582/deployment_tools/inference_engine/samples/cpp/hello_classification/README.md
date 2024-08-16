# Hello Classification C++ Sample {#openvino_inference_engine_samples_hello_classification_README}

This sample demonstrates how to execute an inference of image classification networks like AlexNet and GoogLeNet using Synchronous Inference Request API, input auto-resize feature and support of UNICODE paths.

Hello Classification C++ sample application demonstrates how to use the following Inference Engine C++ API in applications:

| Feature    | API  | Description |
|:---     |:--- |:---
| Basic Infer Flow | `InferenceEngine::Core::ReadNetwork`, `InferenceEngine::Core::LoadNetwork`, `InferenceEngine::ExecutableNetwork::CreateInferRequest`, `InferenceEngine::InferRequest::SetBlob`, `InferenceEngine::InferRequest::GetBlob`  | Common API to do inference: configure input and output blobs, loading model, create infer request
| Synchronous Infer | `InferenceEngine::InferRequest::Infer` | Do synchronous inference
| Network Operations | `ICNNNetwork::getInputsInfo`, `InferenceEngine::CNNNetwork::getOutputsInfo`, `InferenceEngine::InputInfo::setPrecision` |  Managing of network
| Blob Operations| `InferenceEngine::Blob::getTensorDesc`, `InferenceEngine::TensorDesc::getDims`, , `InferenceEngine::TensorDesc::getPrecision`, `InferenceEngine::as`, `InferenceEngine::MemoryBlob::wmap`, `InferenceEngine::MemoryBlob::rmap`, `InferenceEngine::Blob::size` | Work with memory container for storing inputs, outputs of the network, weights and biases of the layers
| Input auto-resize | `InferenceEngine::PreProcessInfo::setResizeAlgorithm`, `InferenceEngine::InputInfo::setLayout` | Set image of the original size as input for a network with other input size. Resize and layout conversions will be performed automatically by the corresponding plugin just before inference

| Options  | Values |
|:---                              |:---
| Validated Models                 | AlexNet and GoogLeNet (image classification networks)
| Model Format                     | Inference Engine Intermediate Representation (\*.xml + \*.bin), ONNX (\*.onnx)
| Validated images                 | The sample uses OpenCV\* to [read input image](https://docs.opencv.org/master/d4/da8/group__imgcodecs.html#ga288b8b3da0892bd651fce07b3bbd3a56) (\*.bmp, \*.png)
| Supported devices                | [All](../../../docs/IE_DG/supported_plugins/Supported_Devices.md) |
| Other language realization       | [C](../../ie_bridges/c/samples/hello_classification/README.md), [Python](../../ie_bridges/python/sample/hello_classification/README.md) |

## How It Works

Upon the start-up, the sample application reads command line parameters, loads specified network and an image to the Inference Engine plugin.
Then, the sample creates an synchronous inference request object. When inference is done, the application outputs data to the standard output stream.

You can see the explicit description of
each sample step at [Integration Steps](../../../docs/IE_DG/Integrate_with_customer_application_new_API.md) section of "Integrate the Inference Engine with Your Application" guide.

## Building

To build the sample, please use instructions available at [Build the Sample Applications](../../../docs/IE_DG/Samples_Overview.md) section in Inference Engine Samples guide.

## Running

To run the sample, you need specify a model and image:

- you can use [public](@ref omz_models_public_index) or [Intel's](@ref omz_models_intel_index) pre-trained models from the Open Model Zoo. The models can be downloaded using the [Model Downloader](@ref omz_tools_downloader_README).
- you can use images from the media files collection available at https://storage.openvinotoolkit.org/data/test_data.

> **NOTES**:
>
> - By default, Inference Engine samples and demos expect input with BGR channels order. If you trained your model to work with RGB order, you need to manually rearrange the default channels order in the sample or demo application or reconvert your model using the Model Optimizer tool with `--reverse_input_channels` argument specified. For more information about the argument, refer to **When to Reverse Input Channels** section of [Converting a Model Using General Conversion Parameters](../../../docs/MO_DG/prepare_model/convert_model/Converting_Model_General.md).
>
> - Before running the sample with a trained model, make sure the model is converted to the Inference Engine format (\*.xml + \*.bin) using the [Model Optimizer tool](../../../docs/MO_DG/Deep_Learning_Model_Optimizer_DevGuide.md).
>
> - The sample accepts models in ONNX format (.onnx) that do not require preprocessing.

You can do inference of an image using a trained AlexNet network on a GPU using the following command:

```sh
./hello_classification <path_to_model>/alexnet_fp32.xml <path_to_image>/car.png GPU
```

## Sample Output

The application outputs top-10 inference results.

```sh
Top 10 results:

Image /opt/intel/openvino/deployment_tools/demo/car.png

classid probability
------- -----------
479     0.7562194  
511     0.0760387  
436     0.0724114  
817     0.0462140  
656     0.0301230  
661     0.0056171  
581     0.0031623  
468     0.0029917  
717     0.0023081  
627     0.0016193  

This sample is an API example, for any performance measurements please use the dedicated benchmark_app tool
```

## See Also

- [Integrate the Inference Engine with Your Application](../../../docs/IE_DG/Integrate_with_customer_application_new_API.md)
- [Using Inference Engine Samples](../../../docs/IE_DG/Samples_Overview.md)
- [Model Downloader](@ref omz_tools_downloader_README)
- [Model Optimizer](../../../docs/MO_DG/Deep_Learning_Model_Optimizer_DevGuide.md)
