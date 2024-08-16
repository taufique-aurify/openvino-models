------------------------------------------------------------------------
Intel(R) Distribution of OpenVINO(TM) tookit for Windows*

Components and their licenses:
* Model Optimizer (Apache 2.0): <install_root>/deployment_tools/model_optimizer/*
* Inference Engine (Intel(R) OpenVINO(TM) Distribution License): <install_root>/deployment_tools/inference_engine/*
    * Inference Engine Headers (Apache 2.0): <install_root>/deployment_tools/inference_engine/include/*
    * Inference Engine Samples (Apache 2.0): <install_root>/deployment_tools/inference_engine/samples/*
    * GNA library (GNA SOFTWARE LICENSE AGREEMENT): <install_root>/deployment_tools/inference_engine/bin/intel64/<Release|Debug>/gna.dll
    * Intel(R) Vision Accelerator Design with Intel(R) Movidius(TM) VPUs (End User License Agreement for the Intel(R) Software Development Products - Floating License): 
	    <install_root>/deployment_tools/inference_engine/external/hddl/*
	    <install_root>/deployment_tools/inference_engine/external/MovidiusDriver/*
    * Intel(R) Movidius(TM) Neural Compute Stick firmware (End User License Agreement for the Intel(R) Software Development Products):
            <install_root>/deployment_tools/inference_engine/bin/intel64/<Release;Debug>/<usb-ma2x8x.mvcmd;pcie-ma2x8x.elf>
* DL Workbench**  (Intel(R) OpenVINO(TM) Distribution License): <install_root>/deployment_tools/tools/workbench*
* Open Model Zoo (Apache 2.0): <install_root>/deployment_tools/open_model_zoo/*
* Post-Training Optimization Tool (Intel(R) OpenVINO(TM) Distribution License): <install_root>/deployment_tools/tools/post_training_optimization_tool/*
* OpenCV (Apache 2.0): <install_root>/opencv/*
* Speech Libraries and End-to-End Speech Demos (GNA SOFTWARE LICENSE AGREEMENT): <install_root>/data_processing/audio/speech_recognition/*
* Installer (End User License Agreement for the Intel(R) Software Development Products): C:\ProgramData\Intel\installer\openvino\cache

------------------------------------------------------------------------
Intel(R) Distribution of OpenVINO(TM) tookit for Linux*

Components and their licenses:
* Model Optimizer (Apache 2.0): <install_root>/deployment_tools/model_optimizer/*
* Inference Engine (Intel(R) OpenVINO(TM) Distribution License): <install_root>/deployment_tools/inference_engine/*
    * Inference Engine Headers (Apache 2.0): <install_root>/deployment_tools/inference_engine/include/*
    * Inference Engine Samples (Apache 2.0): <install_root>/deployment_tools/inference_engine/samples/*
    * GNA library (GNA SOFTWARE LICENSE AGREEMENT): <install_root>/deployment_tools/inference_engine/external/gna/lib/libgna.so*
    * Intel(R) Vision Accelerator Design with Intel(R) Movidius(TM) VPUs (End User License Agreement for the Intel(R) Software Development Products - Floating License): 
	    <install_root>/deployment_tools/inference_engine/external/hddl/*
    * Intel(R) Movidius(TM) Neural Compute Stick firmware (End User License Agreement for the Intel(R) Software Development Products):
            <install_root>/deployment_tools/inference_engine/lib/intel64/<usb-ma2x8x.mvcmd;pcie-ma2x8x.mvcmd>
* DL Workbench** (Intel(R) OpenVINO(TM) Distribution License): <install_root>/deployment_tools/tools/workbench*
* Open Model Zoo (Apache 2.0): <install_root>/deployment_tools/open_model_zoo/*
* Post-Training Optimization Tool (Intel(R) OpenVINO(TM) Distribution License): <install_root>/deployment_tools/tools/post_training_optimization_tool/*
* OpenCV (Apache 2.0): <install_root>/opencv/*
* Speech Libraries and End-to-End Speech Demos (GNA SOFTWARE LICENSE AGREEMENT): <install_root>/data_processing/audio/speech_recognition/*
* DL Streamer (End User License Agreement for the Intel(R) Software Development Products): <install_root>/data_processing/dl_streamer/*, 
    GStreamer (LGPL v2): <install_root>/data_processing/gstreamer/*
* Intel(R) Media SDK (MIT): <install_root>/../mediasdk/*
    * Intel(R) Media Driver for VAAPI (MIT and BSD)
* Installer (End User License Agreement for the Intel(R) Software Development Products): <install_root>/openvino_toolkit_uninstaller/*

------------------------------------------------------------------------
Intel(R) Distribution of OpenVINO(TM) tookit for macOS*

Components and their licenses:
* Model Optimizer (Apache 2.0): <install_root>/deployment_tools/model_optimizer/*
* Inference Engine (Intel(R) OpenVINO(TM) Distribution License): <install_root>/deployment_tools/inference_engine/*
    * Inference Engine Headers (Apache 2.0): <install_root>/deployment_tools/inference_engine/include/*
    * Inference Engine Samples (Apache 2.0): <install_root>/deployment_tools/inference_engine/samples/*
    * Intel(R) Movidius(TM) Neural Compute Stick firmware (End User License Agreement for the Intel(R) Software Development Products):
            <install_root>/deployment_tools/inference_engine/lib/intel64/<usb-ma2x8x.mvcmd;pcie-ma2x8x.mvcmd>
* DL Workbench** (Intel(R) OpenVINO(TM) Distribution License): <install_root>/deployment_tools/tools/workbench*
* Open Model Zoo (Apache 2.0): <install_root>/deployment_tools/open_model_zoo/*
* Post-Training Optimization Tool (Intel(R) OpenVINO(TM) Distribution License): <install_root>/deployment_tools/tools/post_training_optimization_tool/*
* OpenCV (Apache 2.0): <install_root>/opencv/*
* Installer (End User License Agreement for the Intel(R) Software Development Products: <install_root>/openvino_toolkit_uninstaller/*

------------------------------------------------------------------------

Licenses:
 * Intel(R) OpenVINO(TM) Distribution License: <install_root>/licensing/EULA.rtf or EULA.txt
 * End User License Agreement for the Intel(R) Software Development Products: <install_root>/licensing/Intel_Software_Development_Products.rtf or Intel_Software_Development_Products.txt
 * Apache 2.0 <install_root>/licensing/deployment_tools/Apache_license.txt,  <install_root>/licensing/opencv/Apache_license.txt
 * MIT: The MIT License <install_root>/licensing/install_dependencies/MIT_license.txt
 * GNA SOFTWARE LICENSE AGREEMENT <install_root>/licensing/deployment_tools/GNA SOFTWARE LICENSE AGREEMENT.txt

------------------------------------------------------------------------
Third party programs:
* Model Optimizer: <install_root>/licensing/deployment_tools/model_optimizer/third-party-programs.txt
* Inference Engine: <install_root>/licensing/deployment_tools/third-party-programs.txt
* DL Workbench**: <install_root>/deployment_tools/tools/workbench/docker/third-party-programs.txt
* OpenCV: <install_root>/opencv/third-party-programs.txt
    * <install_root>/opencv/ffmpeg-download.ps1
        FFMPEG wrappers for Windows are not supplied with the distribution.
        If you need to read and write video files on Windows via FFMPEG, please, download the files using the provided script.
        Note, that these wrappers are subjects to LGPL license. The full source code is available at the same repository on GitHub:
        https://github.com/opencv/opencv_3rdparty/tree/ffmpeg/master_<timestamp>_src
* Post-Training Optimization Tool: <install_root>/licensing/deployment_tools/tools/post_training_optimization_tool/third-party-programs.txt
* Open Model Zoo: <install_root>/deployment_tools/open_model_zoo/licensing/third-party-programs.txt
* Speech Libraries and End-to-End Speech Demos: <install_root>/data_processing/audio/speech_recognition/LICENSES.txt
* Documentation: <install_root>/licensing/documentation/third-party-programs.txt
* DL Streamer: <install_root>/data_processing/dl_streamer/licensing/third-party-programs

     GStreamer is an open source framework licensed under LGPL. See https://gstreamer.freedesktop.org/documentation/frequently-asked-questions/licensing.html?gi-language=c.  
     You are solely responsible for determining if your use of Gstreamer requires any additional licenses.  Intel is not responsible for obtaining any such licenses, 
     nor liable for any licensing fees due, in connection with your use of Gstreamer.
     
     FFmpeg is an open source project licensed under LGPL and GPL. See https://www.ffmpeg.org/legal.html. You are solely responsible for determining 
     if your use of FFmpeg requires any additional licenses. Intel is not responsible for obtaining any such licenses, nor liable for any licensing fees due, 
     in connection with your use of FFmpeg.

------------------------------------------------------------------------
Redistributable content:
* Intel(R) Distribution of OpenVINO(TM) tookit: <install_root>/licensing/deployment_tools/redist.txt
* OpenCV: <install_root>/licensing/opencv/redist.txt
* install_dependencies: <install_root>/licensing/install_dependencies/redist.txt

-------------------------------------------------------------

* Other names and brands may be claimed as the property of others.

** DL Workbench is available only as a prebuilt Docker image. Reference to DL Workbench is kept in OpenVINO installation, 
   but now pulls pre-built image from DockerHub instead of building it from the package.