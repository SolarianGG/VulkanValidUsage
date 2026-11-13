# Stage 1 samples (manual review)

seed=20261107; token counts are max over qwen / xlmr / remote.

## section_prose (4436 chunks)

### `sec-349ca3d6f593` (84 tok)

```
{"chunk_id": "sec-349ca3d6f593", "section_id": "_promotion_to_vulkan_1_1_17", "part_idx": 0}
---
[Layers & Extensions (Informative) > List of Deprecated Extensions > VK_KHR_maintenance3 > Promotion to Vulkan 1.1]
All functionality in this extension is included in core Vulkan 1.1, with the KHR suffix omitted. The original type, enum, and command names are still available as aliases of the core functionality.
```

### `sec-4ed567cd7eea` (57 tok)

```
{"chunk_id": "sec-4ed567cd7eea", "section_id": "_new_spir_v_capabilities_42", "part_idx": 0}
---
[Layers & Extensions (Informative) > List of Current Extensions > VK_NV_sample_mask_override_coverage > New SPIR-V Capabilities]
- SampleMaskOverrideCoverageNV
```

### `sec-43ee0a065702` (163 tok)

```
{"chunk_id": "sec-43ee0a065702", "section_id": "_description_177", "part_idx": 0}
---
[Layers & Extensions (Informative) > List of Current Extensions > VK_EXT_shader_split_barrier > Description]
This extension splits OpControlBarrier by exposing two new barrier operations with SPV_EXT_split_barrier:

- OpControlBarrierArriveEXT - notifies that invocation has arrived here

- OpControlBarrierWaitEXT - waits on all invocations before proceeding execution

In the Vulkan context, this allows apps to synchronize Subgroup execution flow within a Workgroup without requiring all Subgroups to wait at the arrival condition before proceeding to execute independent work. It also permits synchronizing memory access like other control barriers.
```

### `sec-ee28e00cf490` (52 tok)

```
{"chunk_id": "sec-ee28e00cf490", "section_id": "_new_spir_v_capability_3", "part_idx": 0}
---
[Layers & Extensions (Informative) > List of Current Extensions > VK_HUAWEI_cluster_culling_shader > New SPIR-V Capability]
- ClusterCullingShadingHUAWEI
```

### `sec-794fe3db6bd6` (56 tok)

```
{"chunk_id": "sec-794fe3db6bd6", "section_id": "_version_history_64", "part_idx": 0}
---
[Layers & Extensions (Informative) > List of Current Extensions > VK_KHR_swapchain_mutable_format > Version History]
- Revision 1, 2018-03-28 (Daniel Rakos)

 - Internal revisions.
```

### `sec-e991c85976b3` (206 tok)

```
{"chunk_id": "sec-e991c85976b3", "section_id": "_new_enum_constants_44", "part_idx": 0}
---
[Layers & Extensions (Informative) > List of Current Extensions > VK_KHR_present_id2 > New Enum Constants]
- VK_KHR_PRESENT_ID_2_EXTENSION_NAME

- VK_KHR_PRESENT_ID_2_SPEC_VERSION

- Extending VkStructureType:

 - VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PRESENT_ID_2_FEATURES_KHR

 - VK_STRUCTURE_TYPE_PRESENT_ID_2_KHR

 - VK_STRUCTURE_TYPE_SURFACE_CAPABILITIES_PRESENT_ID_2_KHR

- Extending VkSwapchainCreateFlagBitsKHR:

 - VK_SWAPCHAIN_CREATE_PRESENT_ID_2_BIT_KHR
```

### `sec-7fe011ade798` (232 tok)

```
{"chunk_id": "sec-7fe011ade798", "section_id": "_description_345", "part_idx": 0}
---
[Layers & Extensions (Informative) > List of Deprecated Extensions > VK_KHR_copy_commands2 > Description]
This extension provides extensible versions of the Vulkan buffer and image copy commands. The new commands are functionally identical to the core commands, except that their copy parameters are specified using extensible structures that can be used to pass extension-specific information.

The following extensible copy commands are introduced with this extension: vkCmdCopyBuffer2KHR, vkCmdCopyImage2KHR, vkCmdCopyBufferToImage2KHR, vkCmdCopyImageToBuffer2KHR, vkCmdBlitImage2KHR, and vkCmdResolveImage2KHR. Each command contains an *Info2KHR structure parameter that includes sType/pNext members. Lower level structures describing each region to be copied are also extended with sType/pNext members.
```

### `sec-cfa4dd267c3a` (157 tok)

```
{"chunk_id": "sec-cfa4dd267c3a", "section_id": "_new_bitmasks_27", "part_idx": 0}
---
[Layers & Extensions (Informative) > List of Current Extensions > VK_KHR_video_queue > New Bitmasks]
- VkVideoBeginCodingFlagsKHR

- VkVideoCapabilityFlagsKHR

- VkVideoChromaSubsamplingFlagsKHR

- VkVideoCodecOperationFlagsKHR

- VkVideoCodingControlFlagsKHR

- VkVideoComponentBitDepthFlagsKHR

- VkVideoEndCodingFlagsKHR

- VkVideoSessionCreateFlagsKHR

- VkVideoSessionParametersCreateFlagsKHR
```

### `sec-8886be4d722e` (263 tok)

```
{"chunk_id": "sec-8886be4d722e", "section_id": "shaders-vertex-execution", "part_idx": 0}
---
[Shaders > Vertex Shaders > Vertex Shader Execution]
A vertex shader must be executed at least once for each vertex specified by a drawing command. If the subpass includes multiple views in its view mask, the shader may be invoked separately for each view. During execution, the shader is presented with the index of the vertex and instance for which it has been invoked. Input variables declared in the vertex shader are filled by the implementation with the values of vertex attributes associated with the invocation being executed.

If the same vertex is specified multiple times in a drawing command (e.g. by including the same index value multiple times in an index buffer) the implementation may reuse the results of vertex shading if it can statically determine that the vertex shader invocations will produce identical results.

Note | It is implementation-dependent when and if results of vertex shading are reused, and thus how many times the vertex shader will be executed. This is true also if the vertex shader contains stores or atomic operations (see / vertexPipelineStoresAndAtomics /).
```

### `sec-b15da8e803fb` (169 tok)

```
{"chunk_id": "sec-b15da8e803fb", "section_id": "_version_history_478", "part_idx": 0}
---
[Layers & Extensions (Informative) > List of Deprecated Extensions > VK_QCOM_render_pass_shader_resolve > Version History]
- Revision 1, 2019-06-28 (wwlk)

 - Initial draft

- Revision 2, 2019-11-06 (wwlk)

 - General clean-up/spec updates

 - Added issues

- Revision 3, 2019-11-07 (wwlk)

 - Typos

 - Additional issues

 - Clarified that a shader resolve subpass is the last subpass in a subpass dependency chain

- Revision 4, 2020-01-06 (wwlk)

 - Change resolution of Issue 1 (render_pass, not renderpass)
```

## section_prose_split (865 chunks)

### `sec-0fb41a50ba6c` (724 tok)

```
{"chunk_id": "sec-0fb41a50ba6c", "section_id": "glossary", "part_idx": 13}
---
[Lexicon > Glossary]
A 64-bit, vendor-prefixed, semi-opaque unsigned integer describing vendor-specific details of an image’s memory layout. In Linux graphics APIs, modifiers are commonly used to specify the memory layout of externally shared images. An image has a modifier if and only if it is created with tiling equal to VK_IMAGE_TILING_DRM_FORMAT_MODIFIER_EXT. For more details, refer to the appendix for extension VK_EXT_image_drm_format_modifier.

Local Workgroup

A collection of compute shader invocations invoked by a single dispatching command, which share data via WorkgroupLocal variables and can synchronize with each other.

Logical Device

An object that represents the application’s interface to the physical device. The logical device is the parent of most Vulkan objects. Represented by a VkDevice object.

Logical Operation

Bitwise operations between a fragment color value and a value in a color attachment, that produce a final color value to be written to the attachment.

Lost Device

A state that a logical device may be in as a result of unrecoverable implementation errors, or other exceptional conditions.

Mappable

See Host-Visible Memory.

Memory Dependency

A memory dependency is an execution dependency which includes availability and visibility operations such that:

- The first set of operations happens-before the availability operation

- The availability operation happens-before the visibility operation

- The visibility operation happens-before the second set of operations

Memory Domain

A memory domain is an abstract place to which memory writes are made available by availability operations and memory domain operations. The memory domains correspond to the set of agents that the write can then be made visible to. The memory domains are host, device, shader, workgroup instance (for workgroup instance there is a unique domain for each compute workgroup) and subgroup instance (for subgroup instance there is a unique domain for each subgroup).

Memory Domain Operation

An operation that makes the writes that are available to one memory domain available to another memory domain.

Memory Heap

A region of memory from which device memory allocations can be made.

Memory Type

An index used to select a set of memory properties (e.g. mappable, cached) for a device memory allocation.

Mesh Shading Pipeline

A graphics pipeline where the primitives are assembled explicitly in the shader stages. In contrast to the primitive shading pipeline where
```

### `sec-56c63d1c78e2` (205 tok)

```
{"chunk_id": "sec-56c63d1c78e2", "section_id": "_issues_157", "part_idx": 3}
---
[Layers & Extensions (Informative) > List of Deprecated Extensions > VK_KHR_external_memory > Issues]
RESOLVED: Implementations must ensure that sharing memory objects does not transfer any information between the exporting and importing instances and APIs other than that required to share the data contained in the memory objects explicitly shared. As specific examples, data from previously freed memory objects that used the same underlying physical memory, and data from memory objects using adjacent physical memory must not be visible to applications importing an exported memory object.

9) Must implementations validate external handles the application provides as inputs to memory import operations?

RESOLVED: Implementations must return an error to the application if the provided memory handle cannot be used to complete the requested import operation. However, implementations need not validate handles are of the exact type specified by the application.
```

### `sec-853b56c30cc7` (748 tok)

```
{"chunk_id": "sec-853b56c30cc7", "section_id": "spirvenv-capabilities", "part_idx": 2}
---
[Vulkan Environment for SPIR-V > Capabilities]
SPIR-V OpCapability Vulkan feature, extension, or core version: AtomicFloat32AddEXT / VkPhysicalDeviceShaderAtomicFloatFeaturesEXT /:: / shaderBufferFloat32AtomicAdd / VkPhysicalDeviceShaderAtomicFloatFeaturesEXT /:: / shaderSharedFloat32AtomicAdd / VkPhysicalDeviceShaderAtomicFloatFeaturesEXT /:: / shaderImageFloat32AtomicAdd
SPIR-V OpCapability Vulkan feature, extension, or core version: AtomicFloat64AddEXT / VkPhysicalDeviceShaderAtomicFloatFeaturesEXT /:: / shaderBufferFloat64AtomicAdd / VkPhysicalDeviceShaderAtomicFloatFeaturesEXT /:: / shaderSharedFloat64AtomicAdd
SPIR-V OpCapability Vulkan feature, extension, or core version: AtomicFloat16MinMaxEXT / VkPhysicalDeviceShaderAtomicFloat2FeaturesEXT /:: / shaderBufferFloat16AtomicMinMax / VkPhysicalDeviceShaderAtomicFloat2FeaturesEXT /:: / shaderSharedFloat16AtomicMinMax
SPIR-V OpCapability Vulkan feature, extension, or core version: AtomicFloat32MinMaxEXT / VkPhysicalDeviceShaderAtomicFloat2FeaturesEXT /:: / shaderBufferFloat32AtomicMinMax / VkPhysicalDeviceShaderAtomicFloat2FeaturesEXT /:: / shaderSharedFloat32AtomicMinMax / VkPhysicalDeviceShaderAtomicFloat2FeaturesEXT /:: / shaderImageFloat32AtomicMinMax
SPIR-V OpCapability Vulkan feature, extension, or core version: AtomicFloat64MinMaxEXT / VkPhysicalDeviceShaderAtomicFloat2FeaturesEXT /:: / shaderBufferFloat64AtomicMinMax / VkPhysicalDeviceShaderAtomicFloat2FeaturesEXT /:: / shaderSharedFloat64AtomicMinMax
SPIR-V OpCapability Vulkan feature, extension, or core version: AtomicFloat16VectorNV / VkPhysicalDeviceShaderAtomicFloat16VectorFeaturesNV /:: / shaderFloat16VectorAtomics
SPIR-V OpCapability Vulkan feature, extension, or core version: Int64ImageEXT / VkPhysicalDeviceShaderImageAtomicInt64FeaturesEXT /:: / shaderImageInt64Atomics
SPIR-V OpCapability Vulkan feature, extension, or core version: Int16 / VkPhysicalDeviceFeatures /:: / shaderInt16
```

### `sec-22d5710fe75a` (729 tok)

```
{"chunk_id": "sec-22d5710fe75a", "section_id": "_new_enum_constants_381", "part_idx": 0}
---
[Layers & Extensions (Informative) > List of Deprecated Extensions > VK_KHR_maintenance5 > New Enum Constants]
- VK_KHR_MAINTENANCE_5_EXTENSION_NAME

- VK_KHR_MAINTENANCE_5_SPEC_VERSION

- Extending VkBufferUsageFlagBits2:

 - VK_BUFFER_USAGE_2_INDEX_BUFFER_BIT_KHR

 - VK_BUFFER_USAGE_2_INDIRECT_BUFFER_BIT_KHR

 - VK_BUFFER_USAGE_2_STORAGE_BUFFER_BIT_KHR

 - VK_BUFFER_USAGE_2_STORAGE_TEXEL_BUFFER_BIT_KHR

 - VK_BUFFER_USAGE_2_TRANSFER_DST_BIT_KHR

 - VK_BUFFER_USAGE_2_TRANSFER_SRC_BIT_KHR

 - VK_BUFFER_USAGE_2_UNIFORM_BUFFER_BIT_KHR

 - VK_BUFFER_USAGE_2_UNIFORM_TEXEL_BUFFER_BIT_KHR

 - VK_BUFFER_USAGE_2_VERTEX_BUFFER_BIT_KHR

- Extending VkFormat:

 - VK_FORMAT_A1B5G5R5_UNORM_PACK16_KHR

 - VK_FORMAT_A8_UNORM_KHR

- Extending VkPipelineCreateFlagBits2:

 - VK_PIPELINE_CREATE_2_ALLOW_DERIVATIVES_BIT_KHR

 - VK_PIPELINE_CREATE_2_DERIVATIVE_BIT_KHR

 - VK_PIPELINE_CREATE_2_DISABLE_OPTIMIZATION_BIT_KHR

 - VK_PIPELINE_CREATE_2_DISPATCH_BASE_BIT_KHR

 - VK_PIPELINE_CREATE_2_VIEW_INDEX_FROM_DEVICE_INDEX_BIT_KHR

- Extending VkStructureType:

 - VK_STRUCTURE_TYPE_BUFFER_USAGE_FLAGS_2_CREATE_INFO_KHR

 - VK_STRUCTURE_TYPE_DEVICE_IMAGE_SUBRESOURCE_INFO_KHR

 - VK_STRUCTURE_TYPE_IMAGE_SUBRESOURCE_2_KHR

 - VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_5_FEATURES_KHR

 - VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MAINTENANCE_5_PROPERTIES_KHR

 - VK_STRUCTURE_TYPE_PIPELINE_CREATE_FLAGS_2_CREATE_INFO_KHR

 - VK_STRUCTURE_TYPE_RENDERING_AREA_INFO_KHR
```

### `sec-6ccbed17b127` (755 tok)

```
{"chunk_id": "sec-6ccbed17b127", "section_id": "decode-h264-parameter-sets", "part_idx": 0}
---
[Video Coding > H.264 Decode Operations > H.264 Decode Parameter Sets]
Video session parameters objects created with the video codec operation VK_VIDEO_CODEC_OPERATION_DECODE_H264_BIT_KHR can contain the following types of parameters:

H.264 Sequence Parameter Sets (SPS)

Represented by StdVideoH264SequenceParameterSet structures and interpreted as follows:

- reserved1 and reserved2 are used only for padding purposes and are otherwise ignored;

- seq_parameter_set_id is used as the key of the SPS entry;

- level_idc is one of the enum constants STD_VIDEO_H264_LEVEL_IDC_<major>_<minor> identifying the H.264 level <major>.<minor> as defined in section A.3 of the ITU-T H.264 Specification;

- pOffsetForRefFrame is a pointer to an array of num_ref_frames_in_pic_order_cnt_cycle number of signed integers specifying the elements of the offset_for_ref_frame array, as defined in section 7.4.2.1.1 of the ITU-T H.264 Specification;

- if flags.seq_scaling_matrix_present_flag is set, then the StdVideoH264ScalingLists structure pointed to by pScalingLists is interpreted as follows:

 - scaling_list_present_mask is a bitmask where bit index i corresponds to seq_scaling_list_present_flag[i] as defined in section 7.4.2.1 of the ITU-T H.264 Specification;

 - use_default_scaling_matrix_mask is a bitmask where bit index i corresponds to UseDefaultScalingMatrix4x4Flag[i], when i < 6, or corresponds to UseDefaultScalingMatrix8x8Flag[i-6], otherwise, as defined in section 7.3.2.1 of the ITU-T H.264 Specification;

 - ScalingList4x4 and ScalingList8x8 correspond to the identically named syntax elements defined in section 7.3.2.1 of the ITU-T H.264 Specification;

- if flags.vui_parameters_present_flag is set, then pSequenceParameterSetVui is a pointer to a StdVideoH264SequenceParameterSetVui structure that is interpreted as follows:

 - reserved1 is used only for padding purposes and is otherwise ignored;

 - flags.color_description_present_flag is interpreted as the value of colour_description_present_flag, as defined in section E.2.1 of the ITU-T H.264 Specification;

Note | The name of / colour_description_present_flag / was misspelled in the Video Std header.

 - if flags.nal_hrd_parameters_present_flag or flags.vcl_hrd_parameters_present_flag is set, then the StdVideoH264HrdParameters structure pointed to by pHrdParameters is interpreted as follows:
```

### `sec-6cb4019a64c5` (762 tok)

```
{"chunk_id": "sec-6cb4019a64c5", "section_id": "encode-h265-quantization", "part_idx": 0}
---
[Video Coding > H.265 Encode Operations > H.265 Encode Rate Control > Encode Quantization]
Performing H.265 encode operations involves the process of assigning QP values to individual H.265 coding units. This process depends on the used rate control mode, as well as other encode and rate control parameters, as described below:

- If the configured rate control mode is VK_VIDEO_ENCODE_RATE_CONTROL_MODE_DEFAULT_KHR, then the QP value is initialized by the implementation-specific default rate control algorithm.

 - If the video encode operation is issued with a quantization delta map, the QP delta value corresponding to the coding unit, as fetched from the quantization map, is added to the previously determined QP value. If the fetched QP delta value falls outside the supported QP delta value range reported in the minQpDelta and maxQpDelta members of VkVideoEncodeH265QuantizationMapCapabilitiesKHR, then the QP value used for the coding unit becomes undefined.

- If the configured rate control mode is VK_VIDEO_ENCODE_RATE_CONTROL_MODE_DISABLED_BIT_KHR, then the QP value is initialized from the constant QP value specified for the H.265 slice segment the coding unit is part of.

 - If the video encode operation is issued with a quantization delta map, the QP delta value corresponding to the coding unit, as fetched from the quantization map, is added to the previously determined QP value. If the fetched QP delta value falls outside the supported QP delta value range reported in the minQpDelta and maxQpDelta members of VkVideoEncodeH265QuantizationMapCapabilitiesKHR, then the QP value used for the coding unit becomes undefined.

- If the configured rate control mode is not VK_VIDEO_ENCODE_RATE_CONTROL_MODE_DEFAULT_KHR or VK_VIDEO_ENCODE_RATE_CONTROL_MODE_DISABLED_BIT_KHR, then the QP value is initialized by the corresponding rate control algorithm.

 - If the video encode operation is issued with a quantization delta map, the QP delta value corresponding to the coding unit, as fetched from the quantization map, is added to the previously determined QP value. If the fetched QP delta value falls outside the supported QP delta value range reported in the minQpDelta and maxQpDelta members of VkVideoEncodeH265QuantizationMapCapabilitiesKHR, then the QP value used for the coding unit becomes undefined.

 - If the video encode operation is issued with an emphasis map, the rate control will adjust the QP value based on the emphasis value corresponding to the coding unit, 
```

### `sec-f4143f66e60e` (729 tok)

```
{"chunk_id": "sec-f4143f66e60e", "section_id": "glossary", "part_idx": 4}
---
[Lexicon > Glossary]
The index of a DPB slot within its encompassing DPB.

Decoration (SPIR-V)

Auxiliary information such as built-in variables, stream numbers, invariance, interpolation type, relaxed precision, etc., added to variables or structure-type members through decorations.

Deferrable Command

A command which allows deferred execution of host-side work. See Deferred Host Operations.

Deferrable Operation

A single logical item of host-side work which can be deferred. Represented by the VkDeferredOperationKHR object. See Deferred Host Operations.

Depth/Stencil Attachment

A subpass attachment point, or image view, that is the target of depth and/or stencil test operations and writes.

Depth/Stencil Format

A VkFormat that includes depth and/or stencil components.

Depth/Stencil Image (or ImageView)

A VkImage (or VkImageView) with a depth/stencil format.

Depth/Stencil Resolve Attachment

A subpass attachment point, or image view, that is the target of a multisample resolve operation from the corresponding depth/stencil attachment at the end of the subpass.

Derivative Group

A set of compute, mesh, task, or fragment shader invocations that cooperate to compute derivatives, including implicit derivatives for sampled image operations.

Descriptor

Information about a resource or resource view written into a descriptor set that is used to access the resource or view from a shader.

Descriptor Binding

An entry in a descriptor set layout corresponding to zero or more descriptors of a single descriptor type in a set. Defined by a VkDescriptorSetLayoutBinding structure.

Descriptor Pool

An object that descriptor sets are allocated from, and that owns the storage of those descriptor sets. Descriptor pools aid multithreaded performance by enabling different threads to use different allocators, without internal synchronization on each use. Represented by a VkDescriptorPool object.

Descriptor Set

An object that resource descriptors are written into via the API, and that can be bound to a command buffer such that the descriptors contained within it can be accessed from shaders. Represented by a VkDescriptorSet object.

Descriptor Set Layout

An object defining the set of resources (types and counts) and their relative arrangement (in the binding namespace) within a descriptor set. Used when allocating descriptor sets and when creating pipeline layouts. Represented by a VkDescriptorSetLayout object.

Device

The processor(s) and execution environment th
```

### `sec-1e26a8af955a` (719 tok)

```
{"chunk_id": "sec-1e26a8af955a", "section_id": "spirvenv-capabilities", "part_idx": 8}
---
[Vulkan Environment for SPIR-V > Capabilities]
SPIR-V OpCapability Vulkan feature, extension, or core version: VulkanMemoryModel / VkPhysicalDeviceVulkan12Features /:: / vulkanMemoryModel
SPIR-V OpCapability Vulkan feature, extension, or core version: VulkanMemoryModelDeviceScope / VkPhysicalDeviceVulkan12Features /:: / vulkanMemoryModelDeviceScope
SPIR-V OpCapability Vulkan feature, extension, or core version: DenormPreserve / VkPhysicalDeviceVulkan12Properties /:: / shaderDenormPreserveFloat16 / VkPhysicalDeviceVulkan12Properties /:: / shaderDenormPreserveFloat32 / VkPhysicalDeviceVulkan12Properties /:: / shaderDenormPreserveFloat64
SPIR-V OpCapability Vulkan feature, extension, or core version: DenormFlushToZero / VkPhysicalDeviceVulkan12Properties /:: / shaderDenormFlushToZeroFloat16 / VkPhysicalDeviceVulkan12Properties /:: / shaderDenormFlushToZeroFloat32 / VkPhysicalDeviceVulkan12Properties /:: / shaderDenormFlushToZeroFloat64
SPIR-V OpCapability Vulkan feature, extension, or core version: SignedZeroInfNanPreserve / VkPhysicalDeviceVulkan12Properties /:: / shaderSignedZeroInfNanPreserveFloat16 / VkPhysicalDeviceVulkan12Properties /:: / shaderSignedZeroInfNanPreserveFloat32 / VkPhysicalDeviceVulkan12Properties /:: / shaderSignedZeroInfNanPreserveFloat64
SPIR-V OpCapability Vulkan feature, extension, or core version: RoundingModeRTE / VkPhysicalDeviceVulkan12Properties /:: / shaderRoundingModeRTEFloat16 / VkPhysicalDeviceVulkan12Properties /:: / shaderRoundingModeRTEFloat32 / VkPhysicalDeviceVulkan12Properties /:: / shaderRoundingModeRTEFloat64
SPIR-V OpCapability Vulkan feature, extension, or core version: RoundingModeRTZ / VkPhysicalDeviceVulkan12Properties /:: / shaderRoundingModeRTZFloat16 / VkPhysicalDeviceVulkan12Properties /:: / shaderRoundingModeRTZFloat32 / VkPhysicalDeviceVulkan12Properties /:: / shaderRoundingModeRTZFloat64
```

### `sec-aefc93589592` (726 tok)

```
{"chunk_id": "sec-aefc93589592", "section_id": "_new_enum_constants_81", "part_idx": 0}
---
[Layers & Extensions (Informative) > List of Current Extensions > VK_KHR_video_encode_quantization_map > New Enum Constants]
- VK_KHR_VIDEO_ENCODE_QUANTIZATION_MAP_EXTENSION_NAME

- VK_KHR_VIDEO_ENCODE_QUANTIZATION_MAP_SPEC_VERSION

- Extending VkFormatFeatureFlagBits2:

 - VK_FORMAT_FEATURE_2_VIDEO_ENCODE_EMPHASIS_MAP_BIT_KHR

 - VK_FORMAT_FEATURE_2_VIDEO_ENCODE_QUANTIZATION_DELTA_MAP_BIT_KHR

- Extending VkImageLayout:

 - VK_IMAGE_LAYOUT_VIDEO_ENCODE_QUANTIZATION_MAP_KHR

- Extending VkImageUsageFlagBits:

 - VK_IMAGE_USAGE_VIDEO_ENCODE_EMPHASIS_MAP_BIT_KHR

 - VK_IMAGE_USAGE_VIDEO_ENCODE_QUANTIZATION_DELTA_MAP_BIT_KHR

- Extending VkStructureType:

 - VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VIDEO_ENCODE_QUANTIZATION_MAP_FEATURES_KHR

 - VK_STRUCTURE_TYPE_VIDEO_ENCODE_QUANTIZATION_MAP_CAPABILITIES_KHR

 - VK_STRUCTURE_TYPE_VIDEO_ENCODE_QUANTIZATION_MAP_INFO_KHR

 - VK_STRUCTURE_TYPE_VIDEO_ENCODE_QUANTIZATION_MAP_SESSION_PARAMETERS_CREATE_INFO_KHR

 - VK_STRUCTURE_TYPE_VIDEO_FORMAT_QUANTIZATION_MAP_PROPERTIES_KHR

- Extending VkVideoEncodeCapabilityFlagBitsKHR:

 - VK_VIDEO_ENCODE_CAPABILITY_EMPHASIS_MAP_BIT_KHR

 - VK_VIDEO_ENCODE_CAPABILITY_QUANTIZATION_DELTA_MAP_BIT_KHR

- Extending VkVideoEncodeFlagBitsKHR:

 - VK_VIDEO_ENCODE_WITH_EMPHASIS_MAP_BIT_KHR

 - VK_VIDEO_ENCODE_WITH_QUANTIZATION_DELTA_MAP_BIT_KHR

- Extending VkVideoSessionCreateFlagBitsKHR:

 - VK_VIDEO_SESSION_CREATE_ALLOW_ENCODE_EMPHASIS_MAP_BIT_KHR

 - VK_VIDEO_SESSION_CREATE_ALLOW_ENCODE_QUANTIZATION_DELTA_MAP_BIT_KHR

- Extending VkVideoSessionParametersCreateFlagBitsKHR:

 - VK_VIDEO_SESSION_PARAMETERS_CREATE_QUANTIZATION_MAP_COMPATIBLE_BIT_KHR
```

### `sec-9dfcc09158f5` (516 tok)

```
{"chunk_id": "sec-9dfcc09158f5", "section_id": "formats-packed", "part_idx": 2}
---
[Formats > Format Definition > Packed Formats]
- Packed into 32-bit data types:

 - VK_FORMAT_A8B8G8R8_UNORM_PACK32

 - VK_FORMAT_A8B8G8R8_SNORM_PACK32

 - VK_FORMAT_A8B8G8R8_USCALED_PACK32

 - VK_FORMAT_A8B8G8R8_SSCALED_PACK32

 - VK_FORMAT_A8B8G8R8_UINT_PACK32

 - VK_FORMAT_A8B8G8R8_SINT_PACK32

 - VK_FORMAT_A8B8G8R8_SRGB_PACK32

 - VK_FORMAT_A2R10G10B10_UNORM_PACK32

 - VK_FORMAT_A2R10G10B10_SNORM_PACK32

 - VK_FORMAT_A2R10G10B10_USCALED_PACK32

 - VK_FORMAT_A2R10G10B10_SSCALED_PACK32

 - VK_FORMAT_A2R10G10B10_UINT_PACK32

 - VK_FORMAT_A2R10G10B10_SINT_PACK32

 - VK_FORMAT_A2B10G10R10_UNORM_PACK32

 - VK_FORMAT_A2B10G10R10_SNORM_PACK32

 - VK_FORMAT_A2B10G10R10_USCALED_PACK32

 - VK_FORMAT_A2B10G10R10_SSCALED_PACK32

 - VK_FORMAT_A2B10G10R10_UINT_PACK32

 - VK_FORMAT_A2B10G10R10_SINT_PACK32

 - VK_FORMAT_B10G11R11_UFLOAT_PACK32

 - VK_FORMAT_E5B9G9R9_UFLOAT_PACK32

 - VK_FORMAT_X8_D24_UNORM_PACK32
```

## section_refpage (2724 chunks)

### `sec-e74b2b333440` (306 tok)

```
{"chunk_id": "sec-e74b2b333440", "entity": "VkQueryPoolPerformanceCreateInfoKHR", "section_id": "VkQueryPoolPerformanceCreateInfoKHR", "part_idx": 0}
---
[Queries > Query Pools > VkQueryPoolPerformanceCreateInfoKHR]
The VkQueryPoolPerformanceCreateInfoKHR structure is defined as:

// Provided by VK_KHR_performance_query
typedef struct VkQueryPoolPerformanceCreateInfoKHR {
VkStructureType sType;
const void* pNext;
uint32_t queueFamilyIndex;
uint32_t counterIndexCount;
const uint32_t* pCounterIndices;
} VkQueryPoolPerformanceCreateInfoKHR;

- sType is a VkStructureType value identifying this structure.

- pNext is NULL or a pointer to a structure extending this structure.

- queueFamilyIndex is the queue family index to create this performance query pool for.

- counterIndexCount is the length of the pCounterIndices array.

- pCounterIndices is a pointer to an array of indices into the vkEnumeratePhysicalDeviceQueueFamilyPerformanceQueryCountersKHR::pCounters to enable in this performance query pool.

Structure Chaining:

Extends the structure

- VkQueryPoolCreateInfo
```

### `sec-a868e8330ec2` (474 tok)

```
{"chunk_id": "sec-a868e8330ec2", "entity": "VkPhysicalDeviceOpacityMicromapFeaturesEXT", "section_id": "VkPhysicalDeviceOpacityMicromapFeaturesEXT", "part_idx": 0}
---
[Features > VkPhysicalDeviceOpacityMicromapFeaturesEXT]
The VkPhysicalDeviceOpacityMicromapFeaturesEXT structure is defined as:

// Provided by VK_EXT_opacity_micromap
typedef struct VkPhysicalDeviceOpacityMicromapFeaturesEXT {
VkStructureType sType;
void* pNext;
VkBool32 micromap;
VkBool32 micromapCaptureReplay;
// micromapHostCommands is legacy, but no reason was given in the API XML
VkBool32 micromapHostCommands;
} VkPhysicalDeviceOpacityMicromapFeaturesEXT;

This structure describes the following feature:

- sType is a VkStructureType value identifying this structure.

- pNext is NULL or a pointer to a structure extending this structure.

- micromap indicates whether the implementation supports the micromap array feature.

- micromapCaptureReplay indicates whether the implementation supports capture and replay of addresses for micromap arrays.

- micromapHostCommands indicates whether the implementation supports host side micromap array commands.

If the VkPhysicalDeviceOpacityMicromapFeaturesEXT structure is included in the pNext chain of the VkPhysicalDeviceFeatures2 structure passed to vkGetPhysicalDeviceFeatures2, it is filled in to indicate whether each corresponding feature is supported. If the application wishes to use a VkDevice with any features described by VkPhysicalDeviceOpacityMicromapFeaturesEXT, it must add an instance of the structure, with the desired feature members set to VK_TRUE, to the pNext chain of VkDeviceCreateInfo when creating the VkDevice.

Structure Chaining:

Extends the structures

- VkDeviceCreateInfo

- VkPhysicalDeviceFeatures2
```

### `sec-5b6bf8d16f52` (71 tok)

```
{"chunk_id": "sec-5b6bf8d16f52", "entity": "WorldRayDirectionKHR", "section_id": "WorldRayDirectionKHR", "part_idx": 0}
---
[Shader Interfaces > Built-In Variables > WorldRayDirectionKHR]
WorldRayDirectionKHR

A variable decorated with the WorldRayDirectionKHR decoration will specify the direction of the ray being processed, in world space. The value is the parameter passed into the pipeline trace ray instruction.
```

### `sec-657cee13c32e` (416 tok)

```
{"chunk_id": "sec-657cee13c32e", "entity": "vkCmdDrawMeshTasksIndirectCount2EXT", "section_id": "vkCmdDrawMeshTasksIndirectCount2EXT", "part_idx": 0}
---
[Drawing Commands > Programmable Mesh Shading > vkCmdDrawMeshTasksIndirectCount2EXT]
To record an indirect mesh tasks drawing command with the draw count sourced from an address range, call:

// Provided by VK_KHR_device_address_commands with (VK_KHR_draw_indirect_count or VK_VERSION_1_2) and VK_EXT_mesh_shader
void vkCmdDrawMeshTasksIndirectCount2EXT(
VkCommandBuffer commandBuffer,
const VkDrawIndirectCount2InfoKHR* pInfo);

- commandBuffer is the command buffer into which the command is recorded.

- pInfo is a pointer to a VkDrawIndirectCount2InfoKHR structure defining parameters of this command.

vkCmdDrawMeshTasksIndirectCount2EXT behaves similarly to vkCmdDrawMeshTasksIndirect2EXT except that the draw count is read by the device from an address range during execution. The command will read an unsigned 32-bit integer from pInfo->countAddressRange and use this as the draw count.

Host Synchronization:

- Host access to commandBuffer must be externally synchronized

- Host access to the VkCommandPool that commandBuffer was allocated from must be externally synchronized

Command Properties:

Command Buffer Levels: Primary / Secondary; Render Pass Scope: Inside; Video Coding Scope: Outside; Supported Queue Types: VK_QUEUE_GRAPHICS_BIT; Command Type: Action

Conditional Rendering:

vkCmdDrawMeshTasksIndirectCount2EXT is affected by conditional rendering
```

### `sec-02659c65a668` (341 tok)

```
{"chunk_id": "sec-02659c65a668", "entity": "vkSetPrivateData", "section_id": "vkSetPrivateData", "part_idx": 0}
---
[Private Data > vkSetPrivateData]
To store application-defined data in a slot associated with a Vulkan object, call:

// Provided by VK_VERSION_1_3
VkResult vkSetPrivateData(
VkDevice device,
VkObjectType objectType,
uint64_t objectHandle,
VkPrivateDataSlot privateDataSlot,
uint64_t data);

// Provided by VK_EXT_private_data
// Equivalent to vkSetPrivateData
VkResult vkSetPrivateDataEXT(
VkDevice device,
VkObjectType objectType,
uint64_t objectHandle,
VkPrivateDataSlot privateDataSlot,
uint64_t data);

- device is the device that created the object.

- objectType is a VkObjectType specifying the type of object to associate data with.

- objectHandle is a handle to the object to associate data with.

- privateDataSlot is a handle to a VkPrivateDataSlot specifying location of private data storage.

- data is application-defined data to associate the object with. This data will be stored at privateDataSlot.

Return Codes:

Success

- VK_SUCCESS

Failure

- VK_ERROR_OUT_OF_HOST_MEMORY

- VK_ERROR_UNKNOWN

- VK_ERROR_VALIDATION_FAILED
```

### `sec-ceba614f94f0` (287 tok)

```
{"chunk_id": "sec-ceba614f94f0", "entity": "vkGetDeviceGroupPresentCapabilitiesKHR", "section_id": "vkGetDeviceGroupPresentCapabilitiesKHR", "part_idx": 0}
---
[Window System Integration (WSI) > Device Group Queries > vkGetDeviceGroupPresentCapabilitiesKHR]
A logical device that represents multiple physical devices may support presenting from images on more than one physical device, or combining images from multiple physical devices.

To query these capabilities, call:

// Provided by VK_VERSION_1_1 with VK_KHR_swapchain, VK_KHR_device_group with VK_KHR_surface
VkResult vkGetDeviceGroupPresentCapabilitiesKHR(
VkDevice device,
VkDeviceGroupPresentCapabilitiesKHR* pDeviceGroupPresentCapabilities);

- device is the logical device.

- pDeviceGroupPresentCapabilities is a pointer to a VkDeviceGroupPresentCapabilitiesKHR structure in which the device’s capabilities are returned.

Return Codes:

Success

- VK_SUCCESS

Failure

- VK_ERROR_OUT_OF_DEVICE_MEMORY

- VK_ERROR_OUT_OF_HOST_MEMORY

- VK_ERROR_UNKNOWN

- VK_ERROR_VALIDATION_FAILED
```

### `sec-a84e7a939cf6` (211 tok)

```
{"chunk_id": "sec-a84e7a939cf6", "entity": "VkConformanceVersion", "section_id": "VkConformanceVersion", "part_idx": 0}
---
[Devices and Queues > Physical Devices > VkConformanceVersion]
The conformance test suite version an implementation is compliant with is described with the VkConformanceVersion structure:

// Provided by VK_VERSION_1_2
typedef struct VkConformanceVersion {
uint8_t major;
uint8_t minor;
uint8_t subminor;
uint8_t patch;
} VkConformanceVersion;

// Provided by VK_KHR_driver_properties
// Equivalent to VkConformanceVersion
typedef VkConformanceVersion VkConformanceVersionKHR;

- major is the major version number of the conformance test suite.

- minor is the minor version number of the conformance test suite.

- subminor is the subminor version number of the conformance test suite.

- patch is the patch version number of the conformance test suite.
```

### `sec-8922fe9d62eb` (586 tok)

```
{"chunk_id": "sec-8922fe9d62eb", "entity": "VkShaderFloatControlsIndependence", "section_id": "VkShaderFloatControlsIndependence", "part_idx": 0}
---
[Limits > VkShaderFloatControlsIndependence]
Values which may be returned in the denormBehaviorIndependence and roundingModeIndependence fields of VkPhysicalDeviceFloatControlsProperties are:

// Provided by VK_VERSION_1_2
typedef enum VkShaderFloatControlsIndependence {
VK_SHADER_FLOAT_CONTROLS_INDEPENDENCE_32_BIT_ONLY = 0,
VK_SHADER_FLOAT_CONTROLS_INDEPENDENCE_ALL = 1,
VK_SHADER_FLOAT_CONTROLS_INDEPENDENCE_NONE = 2,
// Provided by VK_KHR_shader_float_controls
VK_SHADER_FLOAT_CONTROLS_INDEPENDENCE_32_BIT_ONLY_KHR = VK_SHADER_FLOAT_CONTROLS_INDEPENDENCE_32_BIT_ONLY,
// Provided by VK_KHR_shader_float_controls
VK_SHADER_FLOAT_CONTROLS_INDEPENDENCE_ALL_KHR = VK_SHADER_FLOAT_CONTROLS_INDEPENDENCE_ALL,
// Provided by VK_KHR_shader_float_controls
VK_SHADER_FLOAT_CONTROLS_INDEPENDENCE_NONE_KHR = VK_SHADER_FLOAT_CONTROLS_INDEPENDENCE_NONE,
} VkShaderFloatControlsIndependence;

// Provided by VK_KHR_shader_float_controls
// Equivalent to VkShaderFloatControlsIndependence
typedef VkShaderFloatControlsIndependence VkShaderFloatControlsIndependenceKHR;

- VK_SHADER_FLOAT_CONTROLS_INDEPENDENCE_32_BIT_ONLY specifies that shader float controls for 32-bit floating-point can be set independently; other bit widths must be set identically to each other.

- VK_SHADER_FLOAT_CONTROLS_INDEPENDENCE_ALL specifies that shader float controls for all bit widths can be set independently.

- VK_SHADER_FLOAT_CONTROLS_INDEPENDENCE_NONE specifies that shader float controls for all bit widths must be set identically.
```

### `sec-68780a1ac5a3` (323 tok)

```
{"chunk_id": "sec-68780a1ac5a3", "entity": "VkClusterAccelerationStructureTypeNV", "section_id": "VkClusterAccelerationStructureTypeNV", "part_idx": 0}
---
[Acceleration Structures > Cluster Level Acceleration Structures > VkClusterAccelerationStructureTypeNV]
Values which can be set in VkClusterAccelerationStructureTypeNV are:

// Provided by VK_NV_cluster_acceleration_structure
typedef enum VkClusterAccelerationStructureTypeNV {
VK_CLUSTER_ACCELERATION_STRUCTURE_TYPE_CLUSTERS_BOTTOM_LEVEL_NV = 0,
VK_CLUSTER_ACCELERATION_STRUCTURE_TYPE_TRIANGLE_CLUSTER_NV = 1,
VK_CLUSTER_ACCELERATION_STRUCTURE_TYPE_TRIANGLE_CLUSTER_TEMPLATE_NV = 2,
} VkClusterAccelerationStructureTypeNV;

- VK_CLUSTER_ACCELERATION_STRUCTURE_TYPE_CLUSTERS_BOTTOM_LEVEL_NV specifies a bottom level cluster acceleration structure.

- VK_CLUSTER_ACCELERATION_STRUCTURE_TYPE_TRIANGLE_CLUSTER_NV specifies a cluster acceleration structure.

- VK_CLUSTER_ACCELERATION_STRUCTURE_TYPE_TRIANGLE_CLUSTER_TEMPLATE_NV specifies a template cluster acceleration structure.
```

### `sec-476e146ffd4c` (422 tok)

```
{"chunk_id": "sec-476e146ffd4c", "entity": "VkMemoryBarrierAccessFlags3KHR", "section_id": "VkMemoryBarrierAccessFlags3KHR", "part_idx": 0}
---
[Synchronization and Cache Control > Execution and Memory Dependencies > Access Types > VkMemoryBarrierAccessFlags3KHR]
An application can link a VkMemoryBarrierAccessFlags3KHR structure in the pNext chain of VkMemoryRangeBarrierKHR, VkMemoryBarrier2, VkBufferMemoryBarrier2, or VkImageMemoryBarrier2 to provide additional access flags beyond those available in VkAccessFlagBits2.

The VkMemoryBarrierAccessFlags3KHR structure is defined as:

// Provided by VK_KHR_maintenance8
typedef struct VkMemoryBarrierAccessFlags3KHR {
VkStructureType sType;
const void* pNext;
VkAccessFlags3KHR srcAccessMask3;
VkAccessFlags3KHR dstAccessMask3;
} VkMemoryBarrierAccessFlags3KHR;

- sType is a VkStructureType value identifying this structure.

- pNext is NULL or a pointer to a structure extending this structure.

- srcAccessMask3 is a VkAccessFlags3KHR mask of access flags to be included in the first access scope.

- dstAccessMask3 is a VkAccessFlags3KHR mask of access flags to be included in the second access scope.

Structure Chaining:

Extends the structures

- VkBufferMemoryBarrier2

- VkImageMemoryBarrier2

- VkMemoryBarrier2

- VkMemoryRangeBarrierKHR

- VkSubpassDependency2
```

## section_refpage_split (1303 chunks)

### `sec-87f1ac4343f9` (132 tok)

```
{"chunk_id": "sec-87f1ac4343f9", "entity": "vkCmdClearAttachments", "section_id": "vkCmdClearAttachments", "part_idx": 1}
---
[Clear Commands > Clearing Images Inside a Render Pass Instance > vkCmdClearAttachments]
- Host access to the VkCommandPool that commandBuffer was allocated from must be externally synchronized

Command Properties:

Command Buffer Levels: Primary / Secondary; Render Pass Scope: Inside; Video Coding Scope: Outside; Supported Queue Types: VK_QUEUE_GRAPHICS_BIT; Command Type: Action

Conditional Rendering:

vkCmdClearAttachments is affected by conditional rendering
```

### `sec-42974cc204c4` (744 tok)

```
{"chunk_id": "sec-42974cc204c4", "entity": "VkSubpassDescription2KHR", "section_id": "VkSubpassDescription2KHR", "part_idx": 0}
---
[Render Pass > Render Pass Creation > VkSubpassDescription2KHR]
The VkSubpassDescription2 structure is defined as:

Warning | This functionality is superseded by / Vulkan Version 1.4 /. See / Legacy Functionality / for more information.

// Provided by VK_VERSION_1_2
typedef struct VkSubpassDescription2 {
VkStructureType sType;
const void* pNext;
VkSubpassDescriptionFlags flags;
VkPipelineBindPoint pipelineBindPoint;
uint32_t viewMask;
uint32_t inputAttachmentCount;
const VkAttachmentReference2* pInputAttachments;
uint32_t colorAttachmentCount;
const VkAttachmentReference2* pColorAttachments;
const VkAttachmentReference2* pResolveAttachments;
const VkAttachmentReference2* pDepthStencilAttachment;
uint32_t preserveAttachmentCount;
const uint32_t* pPreserveAttachments;
} VkSubpassDescription2;

// Provided by VK_KHR_create_renderpass2
// Equivalent to VkSubpassDescription2
typedef VkSubpassDescription2 VkSubpassDescription2KHR;

- sType is a VkStructureType value identifying this structure.

- pNext is NULL or a pointer to a structure extending this structure.

- flags is a bitmask of VkSubpassDescriptionFlagBits specifying usage of the subpass.

- pipelineBindPoint is a VkPipelineBindPoint value specifying the pipeline type supported for this subpass.

- viewMask is a bitfield of view indices describing which views rendering is broadcast to in this subpass, when multiview is enabled.

- inputAttachmentCount is the number of input attachments.

- pInputAttachments is a pointer to an array of VkAttachmentReference2 structures defining the input attachments for this subpass and their layouts.

- colorAttachmentCount is the number of color attachments.

- pColorAttachments is a pointer to an array of colorAttachmentCount VkAttachmentReference2 structures defining the color attachments for this subpass and their layouts.

- pResolveAttachments is NULL or a pointer to an array of colorAttachmentCount VkAttachmentReference2 structures defining the resolve attachments for this subpass and their layouts.

- pDepthStencilAttachment is a pointer to a VkAttachmentReference2 structure specifying the depth/stencil attachment for this subpass and its layout.

- preserveAttachmentCount is the number of preserved attachments.

- pPreserveAttachments is a pointer to an array of preserveAttachmentCount render pass attachment indices identifying attachments that are not used by this subpass, but whose contents must be preserved throughout the subpass.
```

### `sec-12ba27d11e48` (138 tok)

```
{"chunk_id": "sec-12ba27d11e48", "entity": "VkVideoEncodeH264QualityLevelPropertiesKHR", "section_id": "VkVideoEncodeH264QualityLevelPropertiesKHR", "part_idx": 1}
---
[Video Coding > H.264 Encode Operations > H.264 Encode Quality Level Properties > VkVideoEncodeH264QualityLevelPropertiesKHR]
- preferredMaxL1ReferenceCount indicates the preferred maximum number of reference pictures to use in the reference list L1.

- preferredStdEntropyCodingModeFlag indicates the preferred value to use for entropy_coding_mode_flag in StdVideoH264PpsFlags.

Structure Chaining:

Extends the structure

- VkVideoEncodeQualityLevelPropertiesKHR
```

### `sec-3599330d354a` (788 tok)

```
{"chunk_id": "sec-3599330d354a", "entity": "VkShaderStageFlagBits", "section_id": "VkShaderStageFlagBits", "part_idx": 1}
---
[Pipelines > Compute Pipelines > VkShaderStageFlagBits]
// Provided by VK_VERSION_1_0
typedef enum VkShaderStageFlagBits {
VK_SHADER_STAGE_VERTEX_BIT = 0x00000001,
VK_SHADER_STAGE_TESSELLATION_CONTROL_BIT = 0x00000002,
VK_SHADER_STAGE_TESSELLATION_EVALUATION_BIT = 0x00000004,
VK_SHADER_STAGE_GEOMETRY_BIT = 0x00000008,
VK_SHADER_STAGE_FRAGMENT_BIT = 0x00000010,
VK_SHADER_STAGE_COMPUTE_BIT = 0x00000020,
VK_SHADER_STAGE_ALL_GRAPHICS = 0x0000001F,
VK_SHADER_STAGE_ALL = 0x7FFFFFFF,
// Provided by VK_KHR_ray_tracing_pipeline
VK_SHADER_STAGE_RAYGEN_BIT_KHR = 0x00000100,
// Provided by VK_KHR_ray_tracing_pipeline
VK_SHADER_STAGE_ANY_HIT_BIT_KHR = 0x00000200,
// Provided by VK_KHR_ray_tracing_pipeline
VK_SHADER_STAGE_CLOSEST_HIT_BIT_KHR = 0x00000400,
// Provided by VK_KHR_ray_tracing_pipeline
VK_SHADER_STAGE_MISS_BIT_KHR = 0x00000800,
// Provided by VK_KHR_ray_tracing_pipeline
VK_SHADER_STAGE_INTERSECTION_BIT_KHR = 0x00001000,
// Provided by VK_KHR_ray_tracing_pipeline
VK_SHADER_STAGE_CALLABLE_BIT_KHR = 0x00002000,
// Provided by VK_EXT_mesh_shader
VK_SHADER_STAGE_TASK_BIT_EXT = 0x00000040,
// Provided by VK_EXT_mesh_shader
VK_SHADER_STAGE_MESH_BIT_EXT = 0x00000080,
// Provided by VK_HUAWEI_subpass_shading
VK_SHADER_STAGE_SUBPASS_SHADING_BIT_HUAWEI = 0x00004000,
// Provided by VK_HUAWEI_cluster_culling_shader
VK_SHADER_STAGE_CLUSTER_CULLING_BIT_HUAWEI = 0x00080000,
// Provided by VK_NV_ray_tracing
VK_SHADER_STAGE_RAYGEN_BIT_NV = VK_SHADER_STAGE_RAYGEN_BIT_KHR,
// Provided by VK_NV_ray_tracing
VK_SHADER_STAGE_ANY_HIT_BIT_NV = VK_SHADER_STAGE_ANY_HIT_BIT_KHR,
// Provided by VK_NV_ray_tracing
VK_SHADER_STAGE_CLOSEST_HIT_BIT_NV = VK_SHADER_STAGE_CLOSEST_HIT_BIT_KHR,
// Provided by VK_NV_ray_tracing
```

### `sec-efc64519f140` (770 tok)

```
{"chunk_id": "sec-efc64519f140", "section_id": "limits-types", "part_idx": 7}
---
[Limits > Limit Requirements > limits-types]
Type: 3 × / uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxTaskWorkGroupCount; Feature: VK_EXT_mesh_shader
Type: uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxTaskWorkGroupInvocations; Feature: VK_EXT_mesh_shader
Type: 3 × / uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxTaskWorkGroupSize; Feature: VK_EXT_mesh_shader
Type: uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxTaskPayloadSize; Feature: VK_EXT_mesh_shader
Type: uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxTaskSharedMemorySize; Feature: VK_EXT_mesh_shader
Type: uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxTaskPayloadAndSharedMemorySize; Feature: VK_EXT_mesh_shader
Type: uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxMeshWorkGroupTotalCount; Feature: VK_EXT_mesh_shader
Type: 3 × / uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxMeshWorkGroupCount; Feature: VK_EXT_mesh_shader
Type: uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxMeshWorkGroupInvocations; Feature: VK_EXT_mesh_shader
Type: 3 × / uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxMeshWorkGroupSize; Feature: VK_EXT_mesh_shader
Type: uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxMeshSharedMemorySize; Feature: VK_EXT_mesh_shader
Type: uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxMeshPayloadAndSharedMemorySize; Feature: VK_EXT_mesh_shader
Type: uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxMeshOutputMemorySize; Feature: VK_EXT_mesh_shader
Type: uint32_t; Limit: VkPhysicalDeviceMeshShaderPropertiesEXT /:: / maxMeshPayloadAndOutputMemorySize; Feature: VK_EXT_mesh_shader
```

### `sec-f92ec52920c1` (774 tok)

```
{"chunk_id": "sec-f92ec52920c1", "entity": "VkSpirvResourceTypeFlagBitsEXT", "section_id": "VkSpirvResourceTypeFlagBitsEXT", "part_idx": 0}
---
[Descriptor Heaps > Shader Bindings > VkSpirvResourceTypeFlagBitsEXT]
Bits which can be set in VkDescriptorSetAndBindingMappingEXT::resourceMask, are:

// Provided by VK_EXT_descriptor_heap
typedef enum VkSpirvResourceTypeFlagBitsEXT {
VK_SPIRV_RESOURCE_TYPE_ALL_EXT = 0x7FFFFFFF,
VK_SPIRV_RESOURCE_TYPE_SAMPLER_BIT_EXT = 0x00000001,
VK_SPIRV_RESOURCE_TYPE_SAMPLED_IMAGE_BIT_EXT = 0x00000002,
VK_SPIRV_RESOURCE_TYPE_READ_ONLY_IMAGE_BIT_EXT = 0x00000004,
VK_SPIRV_RESOURCE_TYPE_READ_WRITE_IMAGE_BIT_EXT = 0x00000008,
VK_SPIRV_RESOURCE_TYPE_COMBINED_SAMPLED_IMAGE_BIT_EXT = 0x00000010,
VK_SPIRV_RESOURCE_TYPE_UNIFORM_BUFFER_BIT_EXT = 0x00000020,
VK_SPIRV_RESOURCE_TYPE_READ_ONLY_STORAGE_BUFFER_BIT_EXT = 0x00000040,
VK_SPIRV_RESOURCE_TYPE_READ_WRITE_STORAGE_BUFFER_BIT_EXT = 0x00000080,
// Provided by VK_EXT_descriptor_heap with VK_KHR_ray_tracing_pipeline or VK_NV_ray_tracing
VK_SPIRV_RESOURCE_TYPE_ACCELERATION_STRUCTURE_BIT_EXT = 0x00000100,
// Provided by VK_EXT_descriptor_heap with VK_ARM_tensors
VK_SPIRV_RESOURCE_TYPE_TENSOR_BIT_ARM = 0x00000200,
} VkSpirvResourceTypeFlagBitsEXT;

- VK_SPIRV_RESOURCE_TYPE_ALL_EXT specifies that all resource declarations are included.

- VK_SPIRV_RESOURCE_TYPE_SAMPLER_BIT_EXT specifies OpTypeSampler variables.

- VK_SPIRV_RESOURCE_TYPE_SAMPLED_IMAGE_BIT_EXT specifies OpTypeImage variables with a Sampled parameter of 1.

- VK_SPIRV_RESOURCE_TYPE_READ_ONLY_IMAGE_BIT_EXT specifies OpTypeImage variables with a Sampled parameter of 2 and decorated with NonWritable.

- VK_SPIRV_RESOURCE_TYPE_READ_WRITE_IMAGE_BIT_EXT specifies OpTypeImage variables with a Sampled parameter of 2 and not decorated with NonWritable.

- VK_SPIRV_RESOURCE_TYPE_COMBINED_SAMPLED_IMAGE_BIT_EXT specifies OpTypeSampledImage variables.
```

### `sec-c77bdb4c893b` (794 tok)

```
{"chunk_id": "sec-c77bdb4c893b", "entity": "VkStructureType", "section_id": "VkStructureType", "part_idx": 47}
---
[Fundamentals > Common Object Types > Structure Types > VkStructureType]
VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_EARLY_AND_LATE_FRAGMENT_TESTS_FEATURES_AMD = 1000321000,
// Provided by VK_KHR_fragment_shader_barycentric
VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADER_BARYCENTRIC_FEATURES_KHR = 1000203000,
// Provided by VK_KHR_fragment_shader_barycentric with VK_EXT_provoking_vertex
VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADER_BARYCENTRIC_PROPERTIES_KHR = 1000322000,
// Provided by VK_KHR_shader_subgroup_uniform_control_flow
VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SHADER_SUBGROUP_UNIFORM_CONTROL_FLOW_FEATURES_KHR = 1000323000,
// Provided by VK_NV_fragment_shading_rate_enums
VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADING_RATE_ENUMS_PROPERTIES_NV = 1000326000,
// Provided by VK_NV_fragment_shading_rate_enums
VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FRAGMENT_SHADING_RATE_ENUMS_FEATURES_NV = 1000326001,
// Provided by VK_NV_fragment_shading_rate_enums
VK_STRUCTURE_TYPE_PIPELINE_FRAGMENT_SHADING_RATE_ENUM_STATE_CREATE_INFO_NV = 1000326002,
// Provided by VK_NV_ray_tracing_motion_blur
VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_GEOMETRY_MOTION_TRIANGLES_DATA_NV = 1000327000,
// Provided by VK_NV_ray_tracing_motion_blur
VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_RAY_TRACING_MOTION_BLUR_FEATURES_NV = 1000327001,
// Provided by VK_NV_ray_tracing_motion_blur
VK_STRUCTURE_TYPE_ACCELERATION_STRUCTURE_MOTION_INFO_NV = 1000327002,
// Provided by VK_EXT_mesh_shader
VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MESH_SHADER_FEATURES_EXT = 1000328000,
// Provided by VK_EXT_mesh_shader
VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MESH_SHADER_PROPERTIES_EXT = 1000328001,
// Provided by VK_EXT_ycbcr_2plane_444_formats
VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_YCBCR_2_PLANE_444_FORMATS_FEATURES_EXT = 1000330000,
```

### `sec-fa9f039e00e8` (747 tok)

```
{"chunk_id": "sec-fa9f039e00e8", "entity": "VkFormat", "section_id": "VkFormat", "part_idx": 19}
---
[Formats > Format Definition > VkFormat]
- VK_FORMAT_R5G6B5_UNORM_PACK16 specifies a three-component, 16-bit packed unsigned normalized format that has a 5-bit R component in bits 11..15, a 6-bit G component in bits 5..10, and a 5-bit B component in bits 0..4.

- VK_FORMAT_B5G6R5_UNORM_PACK16 specifies a three-component, 16-bit packed unsigned normalized format that has a 5-bit B component in bits 11..15, a 6-bit G component in bits 5..10, and a 5-bit R component in bits 0..4.

- VK_FORMAT_R5G5B5A1_UNORM_PACK16 specifies a four-component, 16-bit packed unsigned normalized format that has a 5-bit R component in bits 11..15, a 5-bit G component in bits 6..10, a 5-bit B component in bits 1..5, and a 1-bit A component in bit 0.

- VK_FORMAT_B5G5R5A1_UNORM_PACK16 specifies a four-component, 16-bit packed unsigned normalized format that has a 5-bit B component in bits 11..15, a 5-bit G component in bits 6..10, a 5-bit R component in bits 1..5, and a 1-bit A component in bit 0.

- VK_FORMAT_A1R5G5B5_UNORM_PACK16 specifies a four-component, 16-bit packed unsigned normalized format that has a 1-bit A component in bit 15, a 5-bit R component in bits 10..14, a 5-bit G component in bits 5..9, and a 5-bit B component in bits 0..4.

- VK_FORMAT_A1B5G5R5_UNORM_PACK16 specifies a four-component, 16-bit packed unsigned normalized format that has a 1-bit A component in bit 15, a 5-bit B component in bits 10..14, a 5-bit G component in bits 5..9, and a 5-bit R component in bits 0..4.

- VK_FORMAT_A8_UNORM specifies a one-component, 8-bit unsigned normalized format that has a single 8-bit A component.

- VK_FORMAT_R8_UNORM specifies a one-component, 8-bit unsigned normalized format that has a single 8-bit R component.

- VK_FORMAT_R8_SNORM specifies a one-component, 8-bit signed normalized format that has a single 8-bit R component.

- VK_FORMAT_R8_USCALED specifies a one-component, 8-bit unsigned scaled integer format that has a single 8-bit R component.

- VK_FORMAT_R8_SSCALED specifies a one-component, 8-bit signed scaled integer format that has a single 8-bit R component.

- VK_FORMAT_R8_UINT specifies a one-component, 8-bit unsigned integer format that has a single 8-bit R component.
```

### `sec-e97c24ef8ac2` (160 tok)

```
{"chunk_id": "sec-e97c24ef8ac2", "entity": "VkResult", "section_id": "VkResult", "part_idx": 0}
---
[Fundamentals > VkResult Return Codes > VkResult]
While the core Vulkan API is not designed to capture incorrect usage, some circumstances still require return codes. Commands in Vulkan return their status via return codes that are in one of two categories:

- Successful completion codes are returned when a command needs to communicate success or status information. All successful completion codes are non-negative values.

- Runtime error codes are returned when a command needs to communicate a failure that could only be detected at runtime. All runtime error codes are negative values.

All return codes in Vulkan are reported via VkResult return values. The possible codes are:
```

### `sec-93a2573fbc3e` (667 tok)

```
{"chunk_id": "sec-93a2573fbc3e", "entity": "VkDescriptorSetLayoutCreateFlagBits", "section_id": "VkDescriptorSetLayoutCreateFlagBits", "part_idx": 1}
---
[Descriptor Sets > Descriptor Set Layout > VkDescriptorSetLayoutCreateFlagBits]
- VK_DESCRIPTOR_SET_LAYOUT_CREATE_UPDATE_AFTER_BIND_POOL_BIT specifies that descriptor sets using this layout must be allocated from a descriptor pool created with the VK_DESCRIPTOR_POOL_CREATE_UPDATE_AFTER_BIND_BIT bit set. Descriptor set layouts created with this bit set have alternate limits for the maximum number of descriptors per-stage and per-pipeline layout. The non-UpdateAfterBind limits only count descriptors in sets created without this flag. The UpdateAfterBind limits count all descriptors, but the limits may be higher than the non-UpdateAfterBind limits.

- VK_DESCRIPTOR_SET_LAYOUT_CREATE_INDIRECT_BINDABLE_BIT_NV specifies that descriptor sets using this layout allows them to be bound with compute pipelines that are created with VK_PIPELINE_CREATE_INDIRECT_BINDABLE_BIT_NV flag set to be used in Device-Generated Commands.

- VK_DESCRIPTOR_SET_LAYOUT_CREATE_DESCRIPTOR_BUFFER_BIT_EXT specifies that this layout must only be used with descriptor buffers.

- VK_DESCRIPTOR_SET_LAYOUT_CREATE_EMBEDDED_IMMUTABLE_SAMPLERS_BIT_EXT specifies that this is a layout only containing immutable samplers that can be bound by vkCmdBindDescriptorBufferEmbeddedSamplersEXT. Unlike normal immutable samplers, embedded immutable samplers do not require the application to provide them in a descriptor buffer.

- VK_DESCRIPTOR_SET_LAYOUT_CREATE_HOST_ONLY_POOL_BIT_EXT specifies that descriptor sets using this layout must be allocated from a descriptor pool created with the VK_DESCRIPTOR_POOL_CREATE_HOST_ONLY_BIT_EXT bit set. Descriptor set layouts created with this bit have no expressible limit for maximum number of descriptors per-stage. Host descriptor sets are limited only by available host memory, but may be limited for implementation specific reasons. Implementations may limit the number of supported descriptors to UpdateAfterBind limits or non-UpdateAfterBind limits, whichever is larger.

- VK_DESCRIPTOR_SET_LAYOUT_CREATE_PER_STAGE_BIT_NV specifies that binding numbers in descriptor sets using this layout may represent different resources and/or types of resources in each stage.
```

## vu_explicit (20575 chunks)

### `VUID-vkCmdDrawIndirectByteCountEXT-coverageModulationTableEnable-07488` (213 tok)

```
{"chunk_id": "VUID-vkCmdDrawIndirectByteCountEXT-coverageModulationTableEnable-07488", "entity": "vkCmdDrawIndirectByteCountEXT", "section_id": "vkCmdDrawIndirectByteCountEXT", "part_idx": 0, "equiv_class_id": "eq-vkCmdDraw-coverageModulationTableEnable-07488", "condition": "VK_EXT_extended_dynamic_state3+VK_EXT_transform_feedback+VK_NV_framebuffer_mixed_samples,VK_EXT_shader_object+VK_EXT_transform_feedback+VK_NV_framebuffer_mixed_samples"}
---
VUID-vkCmdDrawIndirectByteCountEXT-coverageModulationTableEnable-07488
[vkCmdDrawIndirectByteCountEXT] [coverageModulationTableEnable] [VK_EXT_extended_dynamic_state3, VK_EXT_shader_object, VK_EXT_transform_feedback (+1 more)]
If a shader object is bound to any graphics stage or the bound graphics pipeline state was created with the VK_DYNAMIC_STATE_COVERAGE_MODULATION_TABLE_ENABLE_NV state enabled, and the last call to vkCmdSetCoverageModulationTableEnableNV set coverageModulationTableEnable to VK_TRUE, then the coverageModulationTableCount parameter in the last call to vkCmdSetCoverageModulationTableNV must equal the current rasterizationSamples divided by the number of color samples in the current active color attachment
```

### `VUID-vkCreateComputePipelines-pCreateInfos-11429` (115 tok)

```
{"chunk_id": "VUID-vkCreateComputePipelines-pCreateInfos-11429", "entity": "vkCreateComputePipelines", "section_id": "vkCreateComputePipelines", "part_idx": 0, "equiv_class_id": "eq-vkCreateComputePipelines-pCreateInfos-11429", "condition": "VK_EXT_descriptor_heap"}
---
VUID-vkCreateComputePipelines-pCreateInfos-11429
[vkCreateComputePipelines] [pCreateInfos] [VK_EXT_descriptor_heap]
If any element of pCreateInfos sets VK_PIPELINE_CREATE_2_DESCRIPTOR_HEAP_BIT_EXT and includes embedded sampler mappings, this command must not cause the total number of unique embedded samplers in pipelines and shaders on this device to exceed maxDescriptorHeapEmbeddedSamplers
```

### `VUID-vkCmdTraceRaysNV-unnormalizedCoordinates-09635` (81 tok)

```
{"chunk_id": "VUID-vkCmdTraceRaysNV-unnormalizedCoordinates-09635", "entity": "vkCmdTraceRaysNV", "section_id": "vkCmdTraceRaysNV", "part_idx": 0, "equiv_class_id": "eq-vkCmdDispatch-unnormalizedCoordinates-09635", "condition": "VK_NV_ray_tracing"}
---
VUID-vkCmdTraceRaysNV-unnormalizedCoordinates-09635
[vkCmdTraceRaysNV] [unnormalizedCoordinates] [VK_NV_ray_tracing]
If a VkSampler created with unnormalizedCoordinates equal to VK_TRUE is used to sample a VkImageView as a result of this command, then the image view’s levelCount and layerCount must be 1
```

### `VUID-vkCmdBuildAccelerationStructuresKHR-micromap-11701` (160 tok)

```
{"chunk_id": "VUID-vkCmdBuildAccelerationStructuresKHR-micromap-11701", "entity": "vkCmdBuildAccelerationStructuresKHR", "section_id": "vkCmdBuildAccelerationStructuresKHR", "part_idx": 0, "equiv_class_id": "eq-vkCmdBuildAccelerationStructuresIndirectKHR-micromap-11701", "condition": "VK_KHR_acceleration_structure+VK_KHR_opacity_micromap"}
---
VUID-vkCmdBuildAccelerationStructuresKHR-micromap-11701
[vkCmdBuildAccelerationStructuresKHR] [micromap] [VK_KHR_acceleration_structure, VK_KHR_opacity_micromap]
For any element of pInfos[i].pGeometries or pInfos[i].ppGeometries with a geometryType of VK_GEOMETRY_TYPE_TRIANGLES_KHR, if there is an instance of VkAccelerationStructureTrianglesOpacityMicromapKHR in the geometry.triangles.pNext chain with a valid micromap member, then the micromap member must have been constructed prior to this command’s execution on the device
```

### `VUID-VkTensorViewCreateInfoARM-tensor-09749` (57 tok)

```
{"chunk_id": "VUID-VkTensorViewCreateInfoARM-tensor-09749", "entity": "VkTensorViewCreateInfoARM", "section_id": "VkTensorViewCreateInfoARM", "part_idx": 0, "equiv_class_id": "eq-VkTensorMemoryBarrierARM-tensor-09758", "condition": "VK_ARM_tensors"}
---
VUID-VkTensorViewCreateInfoARM-tensor-09749
[VkTensorViewCreateInfoARM] [tensor] [VK_ARM_tensors]
If tensor is non-sparse then it must be bound completely and contiguously to a single VkDeviceMemory object
```

### `VUID-VkMappedMemoryRange-size-00686` (46 tok)

```
{"chunk_id": "VUID-VkMappedMemoryRange-size-00686", "entity": "VkMappedMemoryRange", "section_id": "VkMappedMemoryRange", "part_idx": 0, "equiv_class_id": "eq-VkMappedMemoryRange-size-00686", "condition": "core"}
---
VUID-VkMappedMemoryRange-size-00686
[VkMappedMemoryRange] [size] [Vulkan 1.0]
If size is equal to VK_WHOLE_SIZE, offset must be within the currently mapped range of memory
```

### `VUID-VkIndirectCommandsLayoutCreateInfoEXT-pTokens-11107` (149 tok)

```
{"chunk_id": "VUID-VkIndirectCommandsLayoutCreateInfoEXT-pTokens-11107", "entity": "VkIndirectCommandsLayoutCreateInfoEXT", "section_id": "VkIndirectCommandsLayoutCreateInfoEXT", "part_idx": 0, "equiv_class_id": "eq-VkIndirectCommandsLayoutCreateInfoEXT-pTokens-11107", "condition": "VK_EXT_device_generated_commands+VK_NV_mesh_shader"}
---
VUID-VkIndirectCommandsLayoutCreateInfoEXT-pTokens-11107
[VkIndirectCommandsLayoutCreateInfoEXT] [pTokens] [VK_EXT_device_generated_commands, VK_NV_mesh_shader]
For any element of pTokens, if type is VK_INDIRECT_COMMANDS_TOKEN_TYPE_DRAW_MESH_TASKS_NV_EXT or VK_INDIRECT_COMMANDS_TOKEN_TYPE_DRAW_MESH_TASKS_COUNT_NV_EXT, then the shaderStages must contain VK_SHADER_STAGE_MESH_BIT_NV
```

### `VUID-vkCmdExecuteCommands-pCommandBuffers-11503` (139 tok)

```
{"chunk_id": "VUID-vkCmdExecuteCommands-pCommandBuffers-11503", "entity": "vkCmdExecuteCommands", "section_id": "vkCmdExecuteCommands", "part_idx": 0, "equiv_class_id": "eq-vkCmdExecuteCommands-pCommandBuffers-11503", "condition": "VK_EXT_custom_resolve+VK_KHR_dynamic_rendering,VK_EXT_custom_resolve+VK_VERSION_1_3"}
---
VUID-vkCmdExecuteCommands-pCommandBuffers-11503
[vkCmdExecuteCommands] [pCommandBuffers] [VK_EXT_custom_resolve, VK_KHR_dynamic_rendering, Vulkan 1.3]
If the current render pass instance was begun with vkCmdBeginRendering and contains a custom resolve, and vkCmdBeginCustomResolveEXT has not been recorded in the render pass instance, then each element of pCommandBuffers must have been recorded with VkCustomResolveCreateInfoEXT::customResolve as VK_FALSE
```

### `VUID-VkCopyMemoryToImageInfo-imageOffset-10056` (151 tok)

```
{"chunk_id": "VUID-VkCopyMemoryToImageInfo-imageOffset-10056", "entity": "VkCopyMemoryToImageInfo", "section_id": "VkCopyMemoryToImageInfo", "part_idx": 0, "equiv_class_id": "eq-VkCopyBufferToImageInfo2-imageOffset-10056", "condition": "VK_EXT_host_image_copy+VK_QCOM_rotated_copy_commands,VK_QCOM_rotated_copy_commands+VK_VERSION_1_4"}
---
VUID-VkCopyMemoryToImageInfo-imageOffset-10056
[VkCopyMemoryToImageInfo] [imageOffset] [VK_EXT_host_image_copy, VK_QCOM_rotated_copy_commands, Vulkan 1.4]
For each element of pRegions, if VkCopyCommandTransformInfoQCOM::transform is equal to VK_SURFACE_TRANSFORM_ROTATE_90_BIT_KHR, the sum of imageOffset.y and extent.width does not equal the height of the subresource specified by imageSubresource, extent.width must be a multiple of the texel block extent height of the VkFormat of dstImage
```

### `VUID-vkCmdDispatchBase-None-11442` (208 tok)

```
{"chunk_id": "VUID-vkCmdDispatchBase-None-11442", "entity": "vkCmdDispatchBase", "section_id": "vkCmdDispatchBase", "part_idx": 0, "equiv_class_id": "eq-vkCmdDispatch-None-11442", "condition": "VK_EXT_descriptor_heap+VK_KHR_device_group,VK_EXT_descriptor_heap+VK_VERSION_1_1"}
---
VUID-vkCmdDispatchBase-None-11442
[vkCmdDispatchBase] [VK_EXT_descriptor_heap, VK_KHR_device_group, Vulkan 1.1]
If a pipeline is bound to the pipeline bind point used by this command, or shader is bound to a shader stage used by this command, and it was created with a descriptor mapping using VK_DESCRIPTOR_MAPPING_SOURCE_PUSH_ADDRESS_EXT, VK_DESCRIPTOR_MAPPING_SOURCE_SHADER_RECORD_ADDRESS_EXT, or VK_DESCRIPTOR_MAPPING_SOURCE_INDIRECT_ADDRESS_EXT, and a shader accesses a storage buffer using that mapping, the address that the storage buffer is mapped to must be aligned to minStorageBufferOffsetAlignment
```

## vu_implicit (6854 chunks)

### `VUID-vkCreateFramebuffer-device-queuecount` (32 tok)

```
{"chunk_id": "VUID-vkCreateFramebuffer-device-queuecount", "entity": "vkCreateFramebuffer", "section_id": "vkCreateFramebuffer", "part_idx": 0, "equiv_class_id": "eq-vkCreateFramebuffer-device-queuecount"}
---
VUID-vkCreateFramebuffer-device-queuecount
[vkCreateFramebuffer] [device] [Vulkan 1.0]
The device must have been created with at least 1 queue
```

### `VUID-VkProtectedSubmitInfo-sType-sType` (42 tok)

```
{"chunk_id": "VUID-VkProtectedSubmitInfo-sType-sType", "entity": "VkProtectedSubmitInfo", "section_id": "VkProtectedSubmitInfo", "part_idx": 0, "equiv_class_id": "eq-VkProtectedSubmitInfo-sType-sType"}
---
VUID-VkProtectedSubmitInfo-sType-sType
[VkProtectedSubmitInfo] [sType] [Vulkan 1.1]
sType must be VK_STRUCTURE_TYPE_PROTECTED_SUBMIT_INFO
```

### `VUID-VkHdrMetadataEXT-sType-unique` (43 tok)

```
{"chunk_id": "VUID-VkHdrMetadataEXT-sType-unique", "entity": "VkHdrMetadataEXT", "section_id": "VkHdrMetadataEXT", "part_idx": 0, "equiv_class_id": "eq-VkHdrMetadataEXT-sType-unique"}
---
VUID-VkHdrMetadataEXT-sType-unique
[VkHdrMetadataEXT] [sType] [VK_EXT_hdr_metadata]
The sType value of each structure in the pNext chain must be unique
```

### `VUID-vkCmdSetExtraPrimitiveOverestimationSizeEXT-videocoding` (61 tok)

```
{"chunk_id": "VUID-vkCmdSetExtraPrimitiveOverestimationSizeEXT-videocoding", "entity": "vkCmdSetExtraPrimitiveOverestimationSizeEXT", "section_id": "vkCmdSetExtraPrimitiveOverestimationSizeEXT", "part_idx": 0, "equiv_class_id": "eq-vkCmdSetExtraPrimitiveOverestimationSizeEXT-videocoding"}
---
VUID-vkCmdSetExtraPrimitiveOverestimationSizeEXT-videocoding
[vkCmdSetExtraPrimitiveOverestimationSizeEXT] [VK_EXT_extended_dynamic_state3 or VK_EXT_shader_object]
This command must only be called outside of a video coding scope
```

### `VUID-VkPresentInfoKHR-swapchainCount-arraylength` (36 tok)

```
{"chunk_id": "VUID-VkPresentInfoKHR-swapchainCount-arraylength", "entity": "VkPresentInfoKHR", "section_id": "VkPresentInfoKHR", "part_idx": 0, "equiv_class_id": "eq-VkPresentInfoKHR-swapchainCount-arraylength"}
---
VUID-VkPresentInfoKHR-swapchainCount-arraylength
[VkPresentInfoKHR] [swapchainCount] [VK_KHR_swapchain]
swapchainCount must be greater than 0
```

### `VUID-VkSamplerCaptureDescriptorDataInfoEXT-sampler-parameter` (42 tok)

```
{"chunk_id": "VUID-VkSamplerCaptureDescriptorDataInfoEXT-sampler-parameter", "entity": "VkSamplerCaptureDescriptorDataInfoEXT", "section_id": "VkSamplerCaptureDescriptorDataInfoEXT", "part_idx": 0, "equiv_class_id": "eq-VkSamplerCaptureDescriptorDataInfoEXT-sampler-parameter"}
---
VUID-VkSamplerCaptureDescriptorDataInfoEXT-sampler-parameter
[VkSamplerCaptureDescriptorDataInfoEXT] [sampler] [VK_EXT_descriptor_buffer]
sampler must be a valid VkSampler handle
```

### `VUID-vkSetBufferCollectionImageConstraintsFUCHSIA-collection-parameter` (53 tok)

```
{"chunk_id": "VUID-vkSetBufferCollectionImageConstraintsFUCHSIA-collection-parameter", "entity": "vkSetBufferCollectionImageConstraintsFUCHSIA", "section_id": "vkSetBufferCollectionImageConstraintsFUCHSIA", "part_idx": 0, "equiv_class_id": "eq-vkSetBufferCollectionImageConstraintsFUCHSIA-collection-parameter"}
---
VUID-vkSetBufferCollectionImageConstraintsFUCHSIA-collection-parameter
[vkSetBufferCollectionImageConstraintsFUCHSIA] [collection] [VK_FUCHSIA_buffer_collection]
collection must be a valid VkBufferCollectionFUCHSIA handle
```

### `VUID-vkCmdSetViewport-commandBuffer-cmdpool` (53 tok)

```
{"chunk_id": "VUID-vkCmdSetViewport-commandBuffer-cmdpool", "entity": "vkCmdSetViewport", "section_id": "vkCmdSetViewport", "part_idx": 0, "equiv_class_id": "eq-vkCmdSetViewport-commandBuffer-cmdpool"}
---
VUID-vkCmdSetViewport-commandBuffer-cmdpool
[vkCmdSetViewport] [commandBuffer] [Vulkan 1.0]
The VkCommandPool that commandBuffer was allocated from must support VK_QUEUE_GRAPHICS_BIT operations
```

### `VUID-vkGetPhysicalDeviceSurfaceSupportKHR-commonparent` (56 tok)

```
{"chunk_id": "VUID-vkGetPhysicalDeviceSurfaceSupportKHR-commonparent", "entity": "vkGetPhysicalDeviceSurfaceSupportKHR", "section_id": "vkGetPhysicalDeviceSurfaceSupportKHR", "part_idx": 0, "equiv_class_id": "eq-vkGetPhysicalDeviceSurfaceSupportKHR-commonparent"}
---
VUID-vkGetPhysicalDeviceSurfaceSupportKHR-commonparent
[vkGetPhysicalDeviceSurfaceSupportKHR] [VK_KHR_surface]
Both of physicalDevice, and surface must have been created, allocated, or retrieved from the same VkInstance
```

### `VUID-VkBindVertexBufferIndirectCommandNV-bufferAddress-parameter` (49 tok)

```
{"chunk_id": "VUID-VkBindVertexBufferIndirectCommandNV-bufferAddress-parameter", "entity": "VkBindVertexBufferIndirectCommandNV", "section_id": "VkBindVertexBufferIndirectCommandNV", "part_idx": 0, "equiv_class_id": "eq-VkBindVertexBufferIndirectCommandNV-bufferAddress-parameter"}
---
VUID-VkBindVertexBufferIndirectCommandNV-bufferAddress-parameter
[VkBindVertexBufferIndirectCommandNV] [bufferAddress] [VK_NV_device_generated_commands]
bufferAddress must be a valid VkDeviceAddress value
```

## 10 largest equivalence classes

### `eq-vkCmdDispatch-None-08606`: 40 VUs, 1 distinct suffixes, 1 distinct texts

Entities: vkCmdDispatch, vkCmdDispatchBase, vkCmdDispatchDataGraphARM, vkCmdDispatchGraphAMDX, vkCmdDispatchGraphIndirectAMDX, vkCmdDispatchGraphIndirectCountAMDX, vkCmdDispatchIndirect, vkCmdDispatchIndirect2KHR, vkCmdDispatchTileQCOM, vkCmdDraw, vkCmdDrawClusterHUAWEI, vkCmdDrawClusterIndirectHUAWEI, vkCmdDrawIndexed, vkCmdDrawIndexedIndirect, vkCmdDrawIndexedIndirect2KHR, vkCmdDrawIndexedIndirectCount, vkCmdDrawIndexedIndirectCount2KHR, vkCmdDrawIndirect, vkCmdDrawIndirect2KHR, vkCmdDrawIndirectByteCount2EXT, vkCmdDrawIndirectByteCountEXT, vkCmdDrawIndirectCount, vkCmdDrawIndirectCount2KHR, vkCmdDrawMeshTasksEXT, vkCmdDrawMeshTasksIndirect2EXT, vkCmdDrawMeshTasksIndirectCount2EXT, vkCmdDrawMeshTasksIndirectCountEXT, vkCmdDrawMeshTasksIndirectCountNV, vkCmdDrawMeshTasksIndirectEXT, vkCmdDrawMeshTasksIndirectNV, vkCmdDrawMeshTasksNV, vkCmdDrawMultiEXT, vkCmdDrawMultiIndexedEXT, vkCmdExecuteGeneratedCommandsEXT, vkCmdExecuteGeneratedCommandsNV, vkCmdSubpassShadingHUAWEI, vkCmdTraceRaysIndirect2KHR, vkCmdTraceRaysIndirectKHR, vkCmdTraceRaysKHR, vkCmdTraceRaysNV

```
If the shaderObject feature is not enabled, a valid pipeline must be bound to the pipeline bind point used by this command
```

### `eq-vkCmdDispatch-None-08600`: 40 VUs, 1 distinct suffixes, 1 distinct texts

Entities: vkCmdDispatch, vkCmdDispatchBase, vkCmdDispatchDataGraphARM, vkCmdDispatchGraphAMDX, vkCmdDispatchGraphIndirectAMDX, vkCmdDispatchGraphIndirectCountAMDX, vkCmdDispatchIndirect, vkCmdDispatchIndirect2KHR, vkCmdDispatchTileQCOM, vkCmdDraw, vkCmdDrawClusterHUAWEI, vkCmdDrawClusterIndirectHUAWEI, vkCmdDrawIndexed, vkCmdDrawIndexedIndirect, vkCmdDrawIndexedIndirect2KHR, vkCmdDrawIndexedIndirectCount, vkCmdDrawIndexedIndirectCount2KHR, vkCmdDrawIndirect, vkCmdDrawIndirect2KHR, vkCmdDrawIndirectByteCount2EXT, vkCmdDrawIndirectByteCountEXT, vkCmdDrawIndirectCount, vkCmdDrawIndirectCount2KHR, vkCmdDrawMeshTasksEXT, vkCmdDrawMeshTasksIndirect2EXT, vkCmdDrawMeshTasksIndirectCount2EXT, vkCmdDrawMeshTasksIndirectCountEXT, vkCmdDrawMeshTasksIndirectCountNV, vkCmdDrawMeshTasksIndirectEXT, vkCmdDrawMeshTasksIndirectNV, vkCmdDrawMeshTasksNV, vkCmdDrawMultiEXT, vkCmdDrawMultiIndexedEXT, vkCmdExecuteGeneratedCommandsEXT, vkCmdExecuteGeneratedCommandsNV, vkCmdSubpassShadingHUAWEI, vkCmdTraceRaysIndirect2KHR, vkCmdTraceRaysIndirectKHR, vkCmdTraceRaysKHR, vkCmdTraceRaysNV

```
If a bound shader, or data graph pipeline, was created with a pipeline layout and statically uses a set n, a descriptor set must have been bound to n at the same pipeline bind point, with layouts compatible for set n with the layout(s) used to create the shader, as described in Pipeline Layout Compatibility
```

### `eq-vkCmdDispatch-commandBuffer-02707`: 40 VUs, 1 distinct suffixes, 1 distinct texts

Entities: vkCmdDispatch, vkCmdDispatchBase, vkCmdDispatchDataGraphARM, vkCmdDispatchGraphAMDX, vkCmdDispatchGraphIndirectAMDX, vkCmdDispatchGraphIndirectCountAMDX, vkCmdDispatchIndirect, vkCmdDispatchIndirect2KHR, vkCmdDispatchTileQCOM, vkCmdDraw, vkCmdDrawClusterHUAWEI, vkCmdDrawClusterIndirectHUAWEI, vkCmdDrawIndexed, vkCmdDrawIndexedIndirect, vkCmdDrawIndexedIndirect2KHR, vkCmdDrawIndexedIndirectCount, vkCmdDrawIndexedIndirectCount2KHR, vkCmdDrawIndirect, vkCmdDrawIndirect2KHR, vkCmdDrawIndirectByteCount2EXT, vkCmdDrawIndirectByteCountEXT, vkCmdDrawIndirectCount, vkCmdDrawIndirectCount2KHR, vkCmdDrawMeshTasksEXT, vkCmdDrawMeshTasksIndirect2EXT, vkCmdDrawMeshTasksIndirectCount2EXT, vkCmdDrawMeshTasksIndirectCountEXT, vkCmdDrawMeshTasksIndirectCountNV, vkCmdDrawMeshTasksIndirectEXT, vkCmdDrawMeshTasksIndirectNV, vkCmdDrawMeshTasksNV, vkCmdDrawMultiEXT, vkCmdDrawMultiIndexedEXT, vkCmdExecuteGeneratedCommandsEXT, vkCmdExecuteGeneratedCommandsNV, vkCmdSubpassShadingHUAWEI, vkCmdTraceRaysIndirect2KHR, vkCmdTraceRaysIndirectKHR, vkCmdTraceRaysKHR, vkCmdTraceRaysNV

```
If commandBuffer is an unprotected command buffer and protectedNoFault is not supported, any resource accessed by bound shaders, or a bound data graph pipeline, must not be a protected resource
```

### `eq-vkCmdDispatch-None-08114`: 40 VUs, 1 distinct suffixes, 1 distinct texts

Entities: vkCmdDispatch, vkCmdDispatchBase, vkCmdDispatchDataGraphARM, vkCmdDispatchGraphAMDX, vkCmdDispatchGraphIndirectAMDX, vkCmdDispatchGraphIndirectCountAMDX, vkCmdDispatchIndirect, vkCmdDispatchIndirect2KHR, vkCmdDispatchTileQCOM, vkCmdDraw, vkCmdDrawClusterHUAWEI, vkCmdDrawClusterIndirectHUAWEI, vkCmdDrawIndexed, vkCmdDrawIndexedIndirect, vkCmdDrawIndexedIndirect2KHR, vkCmdDrawIndexedIndirectCount, vkCmdDrawIndexedIndirectCount2KHR, vkCmdDrawIndirect, vkCmdDrawIndirect2KHR, vkCmdDrawIndirectByteCount2EXT, vkCmdDrawIndirectByteCountEXT, vkCmdDrawIndirectCount, vkCmdDrawIndirectCount2KHR, vkCmdDrawMeshTasksEXT, vkCmdDrawMeshTasksIndirect2EXT, vkCmdDrawMeshTasksIndirectCount2EXT, vkCmdDrawMeshTasksIndirectCountEXT, vkCmdDrawMeshTasksIndirectCountNV, vkCmdDrawMeshTasksIndirectEXT, vkCmdDrawMeshTasksIndirectNV, vkCmdDrawMeshTasksNV, vkCmdDrawMultiEXT, vkCmdDrawMultiIndexedEXT, vkCmdExecuteGeneratedCommandsEXT, vkCmdExecuteGeneratedCommandsNV, vkCmdSubpassShadingHUAWEI, vkCmdTraceRaysIndirect2KHR, vkCmdTraceRaysIndirectKHR, vkCmdTraceRaysKHR, vkCmdTraceRaysNV

```
Descriptors in each bound descriptor set, specified via vkCmdBindDescriptorSets, must be valid if they are accessed as described by descriptor validity by the VkPipeline bound to the pipeline bind point used by this command and the bound VkPipeline was not created with VK_PIPELINE_CREATE_DESCRIPTOR_BUFFER_BIT_EXT
```

### `eq-vkCmdDispatch-None-08115`: 40 VUs, 1 distinct suffixes, 1 distinct texts

Entities: vkCmdDispatch, vkCmdDispatchBase, vkCmdDispatchDataGraphARM, vkCmdDispatchGraphAMDX, vkCmdDispatchGraphIndirectAMDX, vkCmdDispatchGraphIndirectCountAMDX, vkCmdDispatchIndirect, vkCmdDispatchIndirect2KHR, vkCmdDispatchTileQCOM, vkCmdDraw, vkCmdDrawClusterHUAWEI, vkCmdDrawClusterIndirectHUAWEI, vkCmdDrawIndexed, vkCmdDrawIndexedIndirect, vkCmdDrawIndexedIndirect2KHR, vkCmdDrawIndexedIndirectCount, vkCmdDrawIndexedIndirectCount2KHR, vkCmdDrawIndirect, vkCmdDrawIndirect2KHR, vkCmdDrawIndirectByteCount2EXT, vkCmdDrawIndirectByteCountEXT, vkCmdDrawIndirectCount, vkCmdDrawIndirectCount2KHR, vkCmdDrawMeshTasksEXT, vkCmdDrawMeshTasksIndirect2EXT, vkCmdDrawMeshTasksIndirectCount2EXT, vkCmdDrawMeshTasksIndirectCountEXT, vkCmdDrawMeshTasksIndirectCountNV, vkCmdDrawMeshTasksIndirectEXT, vkCmdDrawMeshTasksIndirectNV, vkCmdDrawMeshTasksNV, vkCmdDrawMultiEXT, vkCmdDrawMultiIndexedEXT, vkCmdExecuteGeneratedCommandsEXT, vkCmdExecuteGeneratedCommandsNV, vkCmdSubpassShadingHUAWEI, vkCmdTraceRaysIndirect2KHR, vkCmdTraceRaysIndirectKHR, vkCmdTraceRaysKHR, vkCmdTraceRaysNV

```
If the descriptors used by the VkPipeline bound to the pipeline bind point were specified via vkCmdBindDescriptorSets, the bound VkPipeline must have been created without VK_PIPELINE_CREATE_DESCRIPTOR_BUFFER_BIT_EXT
```

### `eq-vkCmdDispatch-None-08116`: 40 VUs, 1 distinct suffixes, 1 distinct texts

Entities: vkCmdDispatch, vkCmdDispatchBase, vkCmdDispatchDataGraphARM, vkCmdDispatchGraphAMDX, vkCmdDispatchGraphIndirectAMDX, vkCmdDispatchGraphIndirectCountAMDX, vkCmdDispatchIndirect, vkCmdDispatchIndirect2KHR, vkCmdDispatchTileQCOM, vkCmdDraw, vkCmdDrawClusterHUAWEI, vkCmdDrawClusterIndirectHUAWEI, vkCmdDrawIndexed, vkCmdDrawIndexedIndirect, vkCmdDrawIndexedIndirect2KHR, vkCmdDrawIndexedIndirectCount, vkCmdDrawIndexedIndirectCount2KHR, vkCmdDrawIndirect, vkCmdDrawIndirect2KHR, vkCmdDrawIndirectByteCount2EXT, vkCmdDrawIndirectByteCountEXT, vkCmdDrawIndirectCount, vkCmdDrawIndirectCount2KHR, vkCmdDrawMeshTasksEXT, vkCmdDrawMeshTasksIndirect2EXT, vkCmdDrawMeshTasksIndirectCount2EXT, vkCmdDrawMeshTasksIndirectCountEXT, vkCmdDrawMeshTasksIndirectCountNV, vkCmdDrawMeshTasksIndirectEXT, vkCmdDrawMeshTasksIndirectNV, vkCmdDrawMeshTasksNV, vkCmdDrawMultiEXT, vkCmdDrawMultiIndexedEXT, vkCmdExecuteGeneratedCommandsEXT, vkCmdExecuteGeneratedCommandsNV, vkCmdSubpassShadingHUAWEI, vkCmdTraceRaysIndirect2KHR, vkCmdTraceRaysIndirectKHR, vkCmdTraceRaysKHR, vkCmdTraceRaysNV

```
Descriptors in bound descriptor buffers, specified via vkCmdSetDescriptorBufferOffsetsEXT, must be valid if they are dynamically used by the VkPipeline bound to the pipeline bind point used by this command and the bound VkPipeline was created with VK_PIPELINE_CREATE_DESCRIPTOR_BUFFER_BIT_EXT
```

### `eq-vkCmdDispatch-None-08117`: 40 VUs, 1 distinct suffixes, 1 distinct texts

Entities: vkCmdDispatch, vkCmdDispatchBase, vkCmdDispatchDataGraphARM, vkCmdDispatchGraphAMDX, vkCmdDispatchGraphIndirectAMDX, vkCmdDispatchGraphIndirectCountAMDX, vkCmdDispatchIndirect, vkCmdDispatchIndirect2KHR, vkCmdDispatchTileQCOM, vkCmdDraw, vkCmdDrawClusterHUAWEI, vkCmdDrawClusterIndirectHUAWEI, vkCmdDrawIndexed, vkCmdDrawIndexedIndirect, vkCmdDrawIndexedIndirect2KHR, vkCmdDrawIndexedIndirectCount, vkCmdDrawIndexedIndirectCount2KHR, vkCmdDrawIndirect, vkCmdDrawIndirect2KHR, vkCmdDrawIndirectByteCount2EXT, vkCmdDrawIndirectByteCountEXT, vkCmdDrawIndirectCount, vkCmdDrawIndirectCount2KHR, vkCmdDrawMeshTasksEXT, vkCmdDrawMeshTasksIndirect2EXT, vkCmdDrawMeshTasksIndirectCount2EXT, vkCmdDrawMeshTasksIndirectCountEXT, vkCmdDrawMeshTasksIndirectCountNV, vkCmdDrawMeshTasksIndirectEXT, vkCmdDrawMeshTasksIndirectNV, vkCmdDrawMeshTasksNV, vkCmdDrawMultiEXT, vkCmdDrawMultiIndexedEXT, vkCmdExecuteGeneratedCommandsEXT, vkCmdExecuteGeneratedCommandsNV, vkCmdSubpassShadingHUAWEI, vkCmdTraceRaysIndirect2KHR, vkCmdTraceRaysIndirectKHR, vkCmdTraceRaysKHR, vkCmdTraceRaysNV

```
If the descriptors used by the VkPipeline bound to the pipeline bind point were specified via vkCmdSetDescriptorBufferOffsetsEXT, the bound VkPipeline must have been created with VK_PIPELINE_CREATE_DESCRIPTOR_BUFFER_BIT_EXT
```

### `eq-vkCmdDispatch-None-08119`: 40 VUs, 1 distinct suffixes, 1 distinct texts

Entities: vkCmdDispatch, vkCmdDispatchBase, vkCmdDispatchDataGraphARM, vkCmdDispatchGraphAMDX, vkCmdDispatchGraphIndirectAMDX, vkCmdDispatchGraphIndirectCountAMDX, vkCmdDispatchIndirect, vkCmdDispatchIndirect2KHR, vkCmdDispatchTileQCOM, vkCmdDraw, vkCmdDrawClusterHUAWEI, vkCmdDrawClusterIndirectHUAWEI, vkCmdDrawIndexed, vkCmdDrawIndexedIndirect, vkCmdDrawIndexedIndirect2KHR, vkCmdDrawIndexedIndirectCount, vkCmdDrawIndexedIndirectCount2KHR, vkCmdDrawIndirect, vkCmdDrawIndirect2KHR, vkCmdDrawIndirectByteCount2EXT, vkCmdDrawIndirectByteCountEXT, vkCmdDrawIndirectCount, vkCmdDrawIndirectCount2KHR, vkCmdDrawMeshTasksEXT, vkCmdDrawMeshTasksIndirect2EXT, vkCmdDrawMeshTasksIndirectCount2EXT, vkCmdDrawMeshTasksIndirectCountEXT, vkCmdDrawMeshTasksIndirectCountNV, vkCmdDrawMeshTasksIndirectEXT, vkCmdDrawMeshTasksIndirectNV, vkCmdDrawMeshTasksNV, vkCmdDrawMultiEXT, vkCmdDrawMultiIndexedEXT, vkCmdExecuteGeneratedCommandsEXT, vkCmdExecuteGeneratedCommandsNV, vkCmdSubpassShadingHUAWEI, vkCmdTraceRaysIndirect2KHR, vkCmdTraceRaysIndirectKHR, vkCmdTraceRaysKHR, vkCmdTraceRaysNV

```
If a descriptor is dynamically used with a VkPipeline created with VK_PIPELINE_CREATE_DESCRIPTOR_BUFFER_BIT_EXT, or a VkShaderEXT created with a VkDescriptorSetLayout that was created with VK_DESCRIPTOR_SET_LAYOUT_CREATE_DESCRIPTOR_BUFFER_BIT_EXT, the descriptor memory must be resident
```

### `eq-vkCmdBeginQuery-commandBuffer-01885`: 39 VUs, 24 distinct suffixes, 1 distinct texts

Entities: vkCmdBeginQuery, vkCmdBeginQueryIndexedEXT, vkCmdBeginShaderInstrumentationARM, vkCmdBuildAccelerationStructuresIndirectKHR, vkCmdBuildAccelerationStructuresKHR, vkCmdCopyMemoryIndirectKHR, vkCmdCopyMemoryToImageIndirectKHR, vkCmdDispatchGraphAMDX, vkCmdDispatchGraphIndirectAMDX, vkCmdDispatchGraphIndirectCountAMDX, vkCmdDispatchIndirect, vkCmdDispatchIndirect2KHR, vkCmdDrawIndexedIndirect, vkCmdDrawIndexedIndirect2KHR, vkCmdDrawIndexedIndirectCount, vkCmdDrawIndexedIndirectCount2KHR, vkCmdDrawIndirect, vkCmdDrawIndirect2KHR, vkCmdDrawIndirectByteCount2EXT, vkCmdDrawIndirectByteCountEXT, vkCmdDrawIndirectCount, vkCmdDrawIndirectCount2KHR, vkCmdDrawMeshTasksIndirect2EXT, vkCmdDrawMeshTasksIndirectCount2EXT, vkCmdDrawMeshTasksIndirectCountEXT, vkCmdDrawMeshTasksIndirectCountNV, vkCmdDrawMeshTasksIndirectEXT, vkCmdDrawMeshTasksIndirectNV, vkCmdEndQuery, vkCmdEndQueryIndexedEXT, vkCmdEndShaderInstrumentationARM, vkCmdExecuteGeneratedCommandsEXT, vkCmdExecuteGeneratedCommandsNV, vkCmdPreprocessGeneratedCommandsEXT, vkCmdPreprocessGeneratedCommandsNV, vkCmdTraceRaysIndirect2KHR, vkCmdTraceRaysIndirectKHR, vkCmdTraceRaysKHR, vkCmdTraceRaysNV

```
commandBuffer must not be a protected command buffer
```

### `eq-vkCmdDispatch-magFilter-04553`: 39 VUs, 1 distinct suffixes, 1 distinct texts

Entities: vkCmdDispatch, vkCmdDispatchBase, vkCmdDispatchGraphAMDX, vkCmdDispatchGraphIndirectAMDX, vkCmdDispatchGraphIndirectCountAMDX, vkCmdDispatchIndirect, vkCmdDispatchIndirect2KHR, vkCmdDispatchTileQCOM, vkCmdDraw, vkCmdDrawClusterHUAWEI, vkCmdDrawClusterIndirectHUAWEI, vkCmdDrawIndexed, vkCmdDrawIndexedIndirect, vkCmdDrawIndexedIndirect2KHR, vkCmdDrawIndexedIndirectCount, vkCmdDrawIndexedIndirectCount2KHR, vkCmdDrawIndirect, vkCmdDrawIndirect2KHR, vkCmdDrawIndirectByteCount2EXT, vkCmdDrawIndirectByteCountEXT, vkCmdDrawIndirectCount, vkCmdDrawIndirectCount2KHR, vkCmdDrawMeshTasksEXT, vkCmdDrawMeshTasksIndirect2EXT, vkCmdDrawMeshTasksIndirectCount2EXT, vkCmdDrawMeshTasksIndirectCountEXT, vkCmdDrawMeshTasksIndirectCountNV, vkCmdDrawMeshTasksIndirectEXT, vkCmdDrawMeshTasksIndirectNV, vkCmdDrawMeshTasksNV, vkCmdDrawMultiEXT, vkCmdDrawMultiIndexedEXT, vkCmdExecuteGeneratedCommandsEXT, vkCmdExecuteGeneratedCommandsNV, vkCmdSubpassShadingHUAWEI, vkCmdTraceRaysIndirect2KHR, vkCmdTraceRaysIndirectKHR, vkCmdTraceRaysKHR, vkCmdTraceRaysNV

```
If a VkSampler created with magFilter or minFilter equal to VK_FILTER_LINEAR, reductionMode equal to VK_SAMPLER_REDUCTION_MODE_WEIGHTED_AVERAGE, and compareEnable equal to VK_FALSE is used to sample a VkImageView as a result of this command, then the image view’s format features must contain VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_LINEAR_BIT
```
