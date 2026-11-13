# Pilot questions for review (pilot)

Leak measures per question: `ngram_content` / `ngram_stop` (without / with stop words, both limited to 5), `fuzz` (character partial ratio, 0-100).

## VUID-VkImageCreateInfo-tiling-04121
- stratum `core_1_0`, entity `VkImageCreateInfo` (api), assigned `yes_no`, verdict `yes`
- **VU:** If tiling is VK_IMAGE_TILING_LINEAR, flags must not contain VK_IMAGE_CREATE_SPARSE_RESIDENCY_BIT

**descriptive** `qp-f03e5133bc-de` (yes_no; ngram 0/0, fuzz 39.5)
- Q: For an image that uses a linear (row-major) texel arrangement, am I required to avoid the creation flag that allows the image to be only partially backed by memory?
- A: Yes. If tiling is VK_IMAGE_TILING_LINEAR, flags must not contain VK_IMAGE_CREATE_SPARSE_RESIDENCY_BIT, so a linear image cannot be partially resident.

**identifier** `qp-42bd7dd9ef-id` (yes_no; ngram 1/1, fuzz 80.2)
- Q: I'm creating an image with tiling = VK_IMAGE_TILING_LINEAR. Must I leave VK_IMAGE_CREATE_SPARSE_RESIDENCY_BIT out of VkImageCreateInfo::flags?
- A: Yes. When tiling is VK_IMAGE_TILING_LINEAR, VkImageCreateInfo::flags must not include VK_IMAGE_CREATE_SPARSE_RESIDENCY_BIT.

## VUID-vkCmdBeginQuery-queryType-00804
- stratum `core_1_0`, entity `vkCmdBeginQuery` (api), assigned `rule`
- **VU:** If the queryType used to create queryPool was VK_QUERY_TYPE_PIPELINE_STATISTICS and any of the pipelineStatistics indicate graphics operations, the VkCommandPool that commandBuffer was allocated from must support graphics operations

**descriptive** `qp-061cf80350-de` (rule; ngram 1/3, fuzz 62.4)
- Q: I start a pipeline statistics query whose enabled counters include ones that count graphics work. What capability does the command pool my command buffer was allocated from need?
- A: The command pool must support graphics operations whenever the pipeline-statistics query pool (VK_QUERY_TYPE_PIPELINE_STATISTICS) has any pipelineStatistics bits indicating graphics operations.
- notes: Question limited to graphics statistics so the compute-statistics rule does not apply.

**identifier** `qp-4e5326f51a-id` (rule; ngram 2/2, fuzz 73.5)
- Q: I call vkCmdBeginQuery on a queryPool of type VK_QUERY_TYPE_PIPELINE_STATISTICS whose pipelineStatistics include counters for graphics operations. What must the VkCommandPool of commandBuffer support?
- A: If the pool was created with VK_QUERY_TYPE_PIPELINE_STATISTICS and any of its pipelineStatistics indicate graphics operations, the VkCommandPool that commandBuffer came from must support graphics operations.
- notes: Question limited to graphics statistics so the compute-statistics rule does not apply.

## VUID-vkCmdClearColorImage-imageLayout-01394
- stratum `core_1_0`, entity `vkCmdClearColorImage` (api), assigned `yes_no`, verdict `no`
- **VU:** imageLayout must be VK_IMAGE_LAYOUT_SHARED_PRESENT_KHR, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL or VK_IMAGE_LAYOUT_GENERAL

**descriptive** `qp-7d6851fa48-de` (yes_no; ngram 0/0, fuzz 42.0)
- Q: Can I clear a color image directly while it sits in the layout optimized for being a transfer source, passing that layout to the clear command?
- A: No. vkCmdClearColorImage only accepts imageLayout values VK_IMAGE_LAYOUT_SHARED_PRESENT_KHR, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL or VK_IMAGE_LAYOUT_GENERAL; VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL is not allowed.

**identifier** `qp-d75cfc8ca0-id` (yes_no; ngram 0/0, fuzz 61.5)
- Q: My image is currently in VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL. Can I call vkCmdClearColorImage on it with imageLayout set to VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL?
- A: No. imageLayout for vkCmdClearColorImage must be one of VK_IMAGE_LAYOUT_SHARED_PRESENT_KHR, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL or VK_IMAGE_LAYOUT_GENERAL, so the image has to be transitioned to one of those first.

## VUID-vkCmdCopyBufferToImage-dstImage-00209
- stratum `core_1_0`, entity `vkCmdCopyBufferToImage` (api), assigned `rule`
- **VU:** For each element of pRegions, if the sum of imageOffset.z and extent.depth does not equal the depth of the subresource specified by srcSubresource, extent.depth must be a multiple of the texel block extent depth of the VkFormat of dstImage

**descriptive** `qp-24045ce9f4-de` (rule; ngram 2/3, fuzz 52.4)
- Q: When uploading from a buffer into a 3D image, if a region's starting depth plus its copied depth does not reach the end of the subresource's depth, what must the copied depth be aligned to?
- A: The region's depth extent must be a multiple of the texel block extent depth of the destination image's format (vkCmdCopyBufferToImage, dstImage).
- notes: VU text says srcSubresource and extent; for this command these correspond to imageSubresource and imageExtent.

**identifier** `qp-cb98ab0dea-id` (rule; ngram 1/3, fuzz 53.2)
- Q: With vkCmdCopyBufferToImage into a 3D dstImage, one region has imageOffset.z + imageExtent.depth that stops short of the subresource's full depth. What alignment does the region's depth extent need then?
- A: In that case the depth of the copy extent must be a multiple of the texel block extent depth of dstImage's VkFormat; the constraint applies only when offset plus depth does not equal the subresource depth.
- notes: VU text says srcSubresource and extent; for this command these correspond to imageSubresource and imageExtent.

## VUID-vkCmdCopyImage-srcImage-01729
- stratum `core_1_0`, entity `vkCmdCopyImage` (api), assigned `yes_no`, verdict `yes`
- **VU:** For each element of pRegions, if the sum of srcOffset.y and extent.height does not equal the height of the subresource specified by srcSubresource, extent.height must be a multiple of the texel block extent height of the VkFormat of srcImage

**descriptive** `qp-824c087d23-de` (yes_no; ngram 1/4, fuzz 50.1)
- Q: I'm copying between two images, and the source uses a block-compressed format. When the copied rectangle stops short of the bottom edge of the source mip level, does the height of the copy then need to be a whole multiple of that format's block height?
- A: Yes. For each region of vkCmdCopyImage, if srcOffset.y + extent.height does not equal the height of the source subresource given by srcSubresource, extent.height must be a multiple of the texel block extent height of the source image's VkFormat; only a region reaching the bottom edge of the subresource is exempt.
- notes: Regenerated; paraphrase avoids the rule's wording.

**identifier** `qp-447f14a302-id` (yes_no; ngram 2/3, fuzz 62.9)
- Q: I'm calling vkCmdCopyImage with a srcImage in a block-compressed format. If a region's srcOffset.y plus extent.height ends above the bottom edge of the srcSubresource, does extent.height have to be a whole multiple of the format's texel block height?
- A: Yes. For each element of pRegions, whenever srcOffset.y + extent.height does not equal the height of the subresource specified by srcSubresource, extent.height must be a multiple of the texel block extent height of the VkFormat of srcImage; only a region that reaches the bottom edge of the subresource is exempt.
- notes: Regenerated; paraphrase avoids the rule's wording.

## VUID-vkCmdDispatchIndirect-buffer-02708
- stratum `core_1_0`, entity `vkCmdDispatchIndirect` (api), assigned `rule`
- **VU:** If buffer is non-sparse then it must be bound completely and contiguously to a single VkDeviceMemory object

**descriptive** `qp-4db260beba-de` (rule; ngram 2/2, fuzz 46.7)
- Q: My compute dispatch reads its workgroup counts from a regular, non-sparse buffer at record time. What has to be true about that buffer's memory binding for the indirect dispatch to be valid?
- A: For vkCmdDispatchIndirect, a non-sparse buffer holding the dispatch parameters must be fully bound, contiguously, to one single VkDeviceMemory allocation.

**identifier** `qp-4cf63f0924-id` (rule; ngram 1/2, fuzz 43.9)
- Q: The buffer I pass to vkCmdDispatchIndirect was created without any sparse flags. What does Vulkan require about how that buffer is bound to memory?
- A: If the buffer passed to vkCmdDispatchIndirect is non-sparse, it must be bound completely and contiguously to a single VkDeviceMemory object.

## VUID-vkCmdDraw-None-07888
- stratum `core_1_0`, entity `vkCmdDraw` (api), assigned `scenario`
- **VU:** If a VK_DESCRIPTOR_TYPE_STORAGE_TEXEL_BUFFER descriptor is accessed using atomic operations as a result of this command, then the storage texel buffer’s format features must contain VK_FORMAT_FEATURE_STORAGE_TEXEL_BUFFER_ATOMIC_BIT

**descriptive** `qp-de5dbeecb2-de` (scenario; ngram 3/3, fuzz 49.4)
- Q: My fragment shader atomically adds to a storage texel buffer whose view uses a single-channel 32-bit unsigned integer format, declared identically in the shader, on a non-sparse buffer. The device says this format supports use as a storage texel buffer but lists no atomic support for it. Is my plain non-indexed draw valid?
- A: No. When a draw accesses a storage texel buffer descriptor with atomic operations, the buffer view's format features must include VK_FORMAT_FEATURE_STORAGE_TEXEL_BUFFER_ATOMIC_BIT; supporting VK_FORMAT_FEATURE_STORAGE_TEXEL_BUFFER_BIT alone is not enough, so this vkCmdDraw is invalid.
- notes: Scenario: 32-bit non-sparse buffer and matching declared format/sampled type avoid the 64-bit sparse, SampledType width, numeric type and without-format VUs.

**identifier** `qp-1bdef10841-id` (scenario; ngram 1/1, fuzz 57.1)
- Q: My fragment shader performs 32-bit atomic adds on a VK_DESCRIPTOR_TYPE_STORAGE_TEXEL_BUFFER whose buffer view uses VK_FORMAT_R32_UINT. The shader's image type declares the matching R32ui format with a 32-bit unsigned sampled type, and the buffer is not sparse. On this device the format's buffer features include VK_FORMAT_FEATURE_STORAGE_TEXEL_BUFFER_BIT but not VK_FORMAT_FEATURE_STORAGE_TEXEL_BUFFER_ATOMIC_BIT. What is wrong with my vkCmdDraw?
- A: Because the storage texel buffer descriptor is accessed with atomic operations during vkCmdDraw, the buffer view's format features must include VK_FORMAT_FEATURE_STORAGE_TEXEL_BUFFER_ATOMIC_BIT. Here VK_FORMAT_R32_UINT only reports VK_FORMAT_FEATURE_STORAGE_TEXEL_BUFFER_BIT, so the atomic access is invalid.
- notes: Scenario: 32-bit non-sparse buffer and matching declared format/sampled type avoid the 64-bit sparse, SampledType width, numeric type and without-format VUs.

## VUID-vkCmdSetScissor-offset-00597
- stratum `core_1_0`, entity `vkCmdSetScissor` (api), assigned `scenario`
- **VU:** Evaluation of (offset.y + extent.height) must not cause a signed integer addition overflow for any element of pScissors

**descriptive** `qp-24e2f850c0-de` (scenario; ngram 1/1, fuzz 38.7)
- Q: While recording a primary graphics command buffer, I dynamically set a single scissor rectangle at index zero: x = 0, y = 100, width 64, height 2147483600. Is that call valid, and if not, why?
- A: It violates the overflow rule for scissor rectangles: for every element of pScissors, offset.y + extent.height must be computable without signed integer addition overflow. Here 100 + 2147483600 exceeds the largest 32-bit signed value (2147483647), so the call is invalid; the horizontal values and the other parameters are fine.

**identifier** `qp-d303b6ab2f-id` (scenario; ngram 1/1, fuzz 40.3)
- Q: In a primary command buffer that is recording (graphics pool, outside video coding) I call vkCmdSetScissor with firstScissor = 0, scissorCount = 1 and one VkRect2D: offset = {0, 100}, extent = {64, 2147483600}. What is wrong with this call?
- A: It violates the overflow rule for scissor rectangles: for every element of pScissors, offset.y + extent.height must be computable without signed integer addition overflow. Here 100 + 2147483600 exceeds the largest 32-bit signed value (2147483647), so the call is invalid; the horizontal values and the other parameters are fine.

## VUID-vkDestroyBuffer-buffer-00922
- stratum `core_1_0`, entity `vkDestroyBuffer` (api), assigned `scenario`
- **VU:** All submitted commands that refer to buffer, either directly or via a VkBufferView, must have completed execution

**descriptive** `qp-47e8a572a9-de` (scenario; ngram 1/1, fuzz 48.7)
- Q: I create a buffer without custom host allocators, make a texel view of it, and submit GPU work that reads through that view. Immediately after submitting, without waiting for completion, I destroy the buffer, again without allocators. Is this allowed?
- A: No. All submitted commands referring to the buffer, directly or via a VkBufferView, must have completed execution before vkDestroyBuffer is called.
- notes: Allocator usage is consistent (NULL at create and destroy), so only the completion rule is violated.

**identifier** `qp-6de2eff3d2-id` (scenario; ngram 1/1, fuzz 49.2)
- Q: I create a VkBuffer with pAllocator = NULL, create a VkBufferView of it, and submit work that reads through that view. Right after vkQueueSubmit returns, before the work is known to have finished, I call vkDestroyBuffer(device, buffer, NULL) on the same device. Is this valid?
- A: No. Before vkDestroyBuffer, every submitted command that refers to buffer, directly or through a VkBufferView, must have completed execution; here the submitted work using the view may still be running.
- notes: Allocator usage is consistent (NULL at create and destroy), so only the completion rule is violated.

## VUID-RuntimeSpirv-shaderRoundingModeRTZFloat16-06305
- stratum `core_promoted`, entity `RuntimeSpirv` (spirv), assigned `rule`
- **VU:** If shaderRoundingModeRTZFloat16 is VK_FALSE, then RoundingModeRTZ for 16-bit floating-point type must not be used

**descriptive** `qp-0e6dc511aa-de` (rule; ngram 1/1, fuzz 44.2)
- Q: The device properties say round-toward-zero is not supported for half-precision floats. What does that restrict in how my shader module declares its rounding behaviour?
- A: When shaderRoundingModeRTZFloat16 is VK_FALSE, the shader must not declare the RoundingModeRTZ execution mode for 16-bit floating-point values.

**identifier** `qp-c086065c9b-id` (rule; ngram 0/1, fuzz 62.8)
- Q: My device reports shaderRoundingModeRTZFloat16 as VK_FALSE. What does that mean for using the RoundingModeRTZ execution mode in my SPIR-V shaders?
- A: When shaderRoundingModeRTZFloat16 is VK_FALSE, a shader must not use the RoundingModeRTZ execution mode for the 16-bit floating-point type; RTZ rounding for half-precision floats is unavailable.

## VUID-VkBlitImageInfo2-dstImage-02000
- stratum `core_promoted`, entity `VkBlitImageInfo2` (api), assigned `yes_no`, verdict `no`
- **VU:** The format features of dstImage must contain VK_FORMAT_FEATURE_BLIT_DST_BIT

**descriptive** `qp-e4ee4b3dee-de` (yes_no; ngram 1/1, fuzz 46.7)
- Q: Is it allowed to blit into a destination image whose format the device reports as usable as a blit source but not as a blit target?
- A: No. For a blit (VkBlitImageInfo2), the format features of dstImage have to contain VK_FORMAT_FEATURE_BLIT_DST_BIT; blit-source support alone does not permit using the image as the destination.

**identifier** `qp-4a415e0fe8-id` (yes_no; ngram 2/2, fuzz 71.6)
- Q: In a VkBlitImageInfo2, can dstImage use a format whose format features include VK_FORMAT_FEATURE_BLIT_SRC_BIT but lack VK_FORMAT_FEATURE_BLIT_DST_BIT?
- A: No. The format features of dstImage are required to include VK_FORMAT_FEATURE_BLIT_DST_BIT; supporting only VK_FORMAT_FEATURE_BLIT_SRC_BIT is not enough for the blit destination.

## VUID-VkCopyImageToBufferInfo2-imageSubresource-09105
- stratum `core_promoted`, entity `VkCopyImageToBufferInfo2` (api), assigned `scenario`
- **VU:** For each element of pRegions, imageSubresource.aspectMask must specify aspects present in srcImage

**descriptive** `qp-a1bc8d77ea-de` (scenario; ngram 0/1, fuzz 43.9)
- Q: I copy a 64x64 single-sample 2D RGBA8 color image (one mip, one layer, transfer-source usage, format supports transfer source, fully bound, in the transfer-source layout) into a buffer with room for the whole image, created for transfer destination. The single region uses buffer offset 0, tightly packed rows, offset zero, extent 64x64x1, mip 0, layer 0, one layer, but selects the depth aspect. What is wrong?
- A: The region selects the depth aspect (VK_IMAGE_ASPECT_DEPTH_BIT) in imageSubresource.aspectMask, but the source color image has no depth aspect. For each element of pRegions, imageSubresource.aspectMask must only specify aspects present in srcImage.

**identifier** `qp-21904f21bf-id` (scenario; ngram 0/1, fuzz 44.9)
- Q: I call vkCmdCopyImageToBuffer2 with srcImage a 64x64 VK_IMAGE_TYPE_2D VK_FORMAT_R8G8B8A8_UNORM image (1 mip, 1 layer, VK_SAMPLE_COUNT_1_BIT, TRANSFER_SRC usage, format supports transfer source, fully bound, in VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL) and dstBuffer a 64 KiB TRANSFER_DST buffer. One VkBufferImageCopy2: bufferOffset 0, bufferRowLength and bufferImageHeight 0, imageOffset {0,0,0}, imageExtent {64,64,1}, imageSubresource {VK_IMAGE_ASPECT_DEPTH_BIT, mip 0, layer 0, count 1}. What is wrong?
- A: The region's imageSubresource.aspectMask is VK_IMAGE_ASPECT_DEPTH_BIT, but srcImage is a color image that has no depth aspect. For each element of pRegions, imageSubresource.aspectMask must only name aspects that srcImage actually has (here VK_IMAGE_ASPECT_COLOR_BIT).

## VUID-VkFramebufferCreateInfo-renderPass-04536
- stratum `core_promoted`, entity `VkFramebufferCreateInfo` (api), assigned `scenario`
- **VU:** If renderPass was specified with non-zero view masks, each element of pAttachments that is used as an input, color, resolve, or depth/stencil attachment by renderPass must have a layerCount greater than the index of the most significant bit set in any of those view masks

**descriptive** `qp-56d6a4aeb3-de` (scenario; ngram 1/1, fuzz 46.1)
- Q: I'm creating a regular (not imageless) framebuffer for a render pass using multiple views; its single subpass renders views 1 and 2 and writes one color attachment. The framebuffer has one layer and matches the image size, and the color view covers mip 0 and two array layers with matching format, sample count and color-attachment usage. Is this valid?
- A: No. When renderPass uses non-zero view masks, each color, input, depth/stencil or resolve attachment view in pAttachments needs a layerCount larger than the index of the highest bit set in those masks. Views 1 and 2 give a highest bit index of 2, so the view must have at least 3 layers; 2 layers violate the rule.
- notes: Imageless flag not set, layers = 1 (multiview requires 1), layerCount 2 >= layers; only the view-mask layer rule is violated.

**identifier** `qp-0a570b4223-id` (scenario; ngram 1/1, fuzz 46.9)
- Q: I create a VkFramebuffer with flags = 0 for a render pass whose only subpass has viewMask 0b0110 and one color attachment. layers is 1, width and height equal the image extent, and the color VkImageView is a 2D array view of mip 0 with layerCount 2, matching format, samples and COLOR_ATTACHMENT usage. Is this valid?
- A: No. With non-zero view masks in renderPass, every color, input, depth/stencil or resolve attachment view in pAttachments needs a layerCount exceeding the highest set bit index of those view masks. viewMask 0b0110 has its highest bit at index 2, so the color view needs at least 3 layers, and layerCount 2 is too few.
- notes: Imageless flag not set, layers = 1 (multiview requires 1), layerCount 2 >= layers; only the view-mask layer rule is violated.

## VUID-VkImageCreateInfo-flags-00950
- stratum `core_promoted`, entity `VkImageCreateInfo` (api), assigned `yes_no`, verdict `yes`
- **VU:** If flags contains VK_IMAGE_CREATE_2D_ARRAY_COMPATIBLE_BIT, imageType must be VK_IMAGE_TYPE_3D

**descriptive** `qp-8b59ebb630-de` (yes_no; ngram 1/1, fuzz 43.0)
- Q: When I create an image with the flag that lets it be viewed as an array of 2D slices, must the image itself be three-dimensional?
- A: Yes. If VkImageCreateInfo::flags contains VK_IMAGE_CREATE_2D_ARRAY_COMPATIBLE_BIT, imageType must be VK_IMAGE_TYPE_3D.

**identifier** `qp-8bae2ebd9c-id` (yes_no; ngram 1/1, fuzz 72.3)
- Q: I'm setting VK_IMAGE_CREATE_2D_ARRAY_COMPATIBLE_BIT in VkImageCreateInfo::flags. Is it required that imageType be VK_IMAGE_TYPE_3D?
- A: Yes. Whenever VkImageCreateInfo::flags includes VK_IMAGE_CREATE_2D_ARRAY_COMPATIBLE_BIT, imageType must be VK_IMAGE_TYPE_3D.

## VUID-VkRenderingInputAttachmentIndexInfo-pColorAttachmentInputIndices-09522
- stratum `core_promoted`, entity `VkRenderingInputAttachmentIndexInfo` (api), assigned `yes_no`, verdict `yes`
- **VU:** Elements of pColorAttachmentInputIndices that are not VK_ATTACHMENT_UNUSED must each be unique

**descriptive** `qp-5a30034c40-de` (yes_no; ngram 2/2, fuzz 55.6)
- Q: When remapping color attachments to shader input attachment indices for local reads in dynamic rendering, must each color attachment that is actually mapped (not marked as unused) receive a distinct index?
- A: Yes. In VkRenderingInputAttachmentIndexInfo, the values in pColorAttachmentInputIndices that are not VK_ATTACHMENT_UNUSED must each be unique.

**identifier** `qp-91121f4f2e-id` (yes_no; ngram 1/4, fuzz 81.9)
- Q: In VkRenderingInputAttachmentIndexInfo, must the entries of pColorAttachmentInputIndices that are not VK_ATTACHMENT_UNUSED all differ from one another?
- A: Yes. Every element of pColorAttachmentInputIndices other than VK_ATTACHMENT_UNUSED has to be unique; only VK_ATTACHMENT_UNUSED may appear more than once.

## VUID-vkCmdBindIndexBuffer2-None-09493
- stratum `core_promoted`, entity `vkCmdBindIndexBuffer2` (api), assigned `rule`
- **VU:** If the maintenance6 feature is not enabled, buffer must not be VK_NULL_HANDLE

**descriptive** `qp-70ad242eee-de` (rule; ngram 1/1, fuzz 59.7)
- Q: When binding an index buffer with the newer bind command that also takes a size, what device feature must be enabled before I may pass a null handle instead of a real buffer?
- A: The maintenance6 feature; without it the buffer passed to vkCmdBindIndexBuffer2 must not be VK_NULL_HANDLE.

**identifier** `qp-6f23709d54-id` (rule; ngram 1/1, fuzz 66.7)
- Q: Which feature has to be enabled for me to pass VK_NULL_HANDLE as the buffer parameter of vkCmdBindIndexBuffer2?
- A: The maintenance6 feature. When maintenance6 is not enabled, buffer in vkCmdBindIndexBuffer2 must not be VK_NULL_HANDLE.

## VUID-vkCmdDrawIndirectCount-pStrides-04913
- stratum `core_promoted`, entity `vkCmdDrawIndirectCount` (api), assigned `rule`
- **VU:** If the bound graphics pipeline was created with the VK_DYNAMIC_STATE_VERTEX_INPUT_BINDING_STRIDE dynamic state enabled, but without the VK_DYNAMIC_STATE_VERTEX_INPUT_EXT dynamic state enabled, then vkCmdBindVertexBuffers2 with a non-NULL pStrides parameter or vkCmdBindVertexBuffers3KHR with setStride set to VK_TRUE must have been called and not subsequently invalidated in the current command buffer prior to this draw command

**descriptive** `qp-14be9f7fd8-de` (rule; ngram 2/2, fuzz 49.3)
- Q: I issue an indirect draw whose draw count is read from a buffer. The pipeline treats only the per-binding vertex stride as dynamic, not the entire vertex input layout. What must I record earlier in the command buffer for this draw to be valid?
- A: If the bound graphics pipeline has VK_DYNAMIC_STATE_VERTEX_INPUT_BINDING_STRIDE enabled but not VK_DYNAMIC_STATE_VERTEX_INPUT_EXT, then before vkCmdDrawIndirectCount the command buffer must contain a still-valid call to vkCmdBindVertexBuffers2 with a non-NULL pStrides, or to vkCmdBindVertexBuffers3KHR with setStride equal to VK_TRUE.

**identifier** `qp-560e6498e1-id` (rule; ngram 2/2, fuzz 64.0)
- Q: My graphics pipeline enables VK_DYNAMIC_STATE_VERTEX_INPUT_BINDING_STRIDE but not VK_DYNAMIC_STATE_VERTEX_INPUT_EXT. What do I need to have recorded in the command buffer before vkCmdDrawIndirectCount so the vertex strides are provided?
- A: If the bound graphics pipeline has VK_DYNAMIC_STATE_VERTEX_INPUT_BINDING_STRIDE enabled but not VK_DYNAMIC_STATE_VERTEX_INPUT_EXT, then before vkCmdDrawIndirectCount the command buffer must contain a still-valid call to vkCmdBindVertexBuffers2 with a non-NULL pStrides, or to vkCmdBindVertexBuffers3KHR with setStride equal to VK_TRUE.

## VUID-vkCmdResetEvent2-stageMask-03929
- stratum `core_promoted`, entity `vkCmdResetEvent2` (api), assigned `scenario`
- **VU:** If the geometryShader feature is not enabled, stageMask must not contain VK_PIPELINE_STAGE_2_GEOMETRY_SHADER_BIT

**descriptive** `qp-10da09acd9-de` (scenario; ngram 2/2, fuzz 51.8)
- Q: On a single-GPU device with the newer synchronization model turned on but geometry shaders not enabled, I record a reset of a valid, never-waited event outside any render pass in a graphics command buffer, naming only the geometry shader stage as the stage. What is wrong?
- A: Since the geometryShader feature is not enabled, the stageMask of vkCmdResetEvent2 must not include VK_PIPELINE_STAGE_2_GEOMETRY_SHADER_BIT, so specifying the geometry shader stage is invalid.
- notes: Same scenario as the identifier line.

**identifier** `qp-54226001a5-id` (scenario; ngram 2/2, fuzz 72.3)
- Q: With synchronization2 enabled but geometryShader not enabled, I record vkCmdResetEvent2(cmd, event, VK_PIPELINE_STAGE_2_GEOMETRY_SHADER_BIT) outside any render pass in a primary graphics command buffer on a single-GPU device; the event is valid and was never waited on. Is this valid?
- A: No. Because the geometryShader feature is not enabled, stageMask passed to vkCmdResetEvent2 must not contain VK_PIPELINE_STAGE_2_GEOMETRY_SHADER_BIT; that stage bit is only permitted when the feature is enabled.
- notes: Scenario fixes synchronization2 enabled, graphics pool, recording state, outside render pass, single device, no prior waits on the event.

## VUID-TaskCountNV-TaskCountNV-04385
- stratum `ext_niche`, entity `TaskCountNV` (builtin), assigned `yes_no`, verdict `no`
- **VU:** The variable decorated with TaskCountNV must be declared using the Output Storage Class

**descriptive** `qp-490a161efb-de` (yes_no; ngram 1/1, fuzz 48.6)
- Q: In a task shader of the older vendor mesh-shading extension, I declare the 32-bit integer built-in that tells how many mesh workgroups get launched once the task shader finishes. Can that variable live in private per-invocation storage?
- A: No. The variable decorated with TaskCountNV must be declared using the Output storage class; private storage is not allowed.

**identifier** `qp-a0125d5647-id` (yes_no; ngram 2/2, fuzz 62.1)
- Q: In my TaskNV shader I declare a 32-bit integer scalar decorated with TaskCountNV. Is it allowed to place that variable in the Private storage class?
- A: No. A variable decorated with TaskCountNV must be declared in the Output storage class, so the Private storage class is not allowed.

## VUID-VkCopyImageInfo2-srcImage-07969
- stratum `ext_niche`, entity `VkCopyImageInfo2` (api), assigned `scenario`
- **VU:** srcImage must not have been created with flags containing VK_IMAGE_CREATE_SUBSAMPLED_BIT_EXT

**descriptive** `qp-a8f8f4fad5-de` (scenario; ngram 1/1, fuzz 47.8)
- Q: Using the extended image-to-image copy command, I copy the whole first mip level and layer of a 2D color image created as subsampled (for fragment density map rendering) into an ordinary 2D image of the same format and size. Usage, format support, memory and layouts are all correct. Is this valid?
- A: No. The source image of VkCopyImageInfo2 (srcImage) must not have been created with VK_IMAGE_CREATE_SUBSAMPLED_BIT_EXT, so a subsampled image cannot be copied from with this command.
- notes: Destination is not subsampled; same type, format, samples; full-subresource region at offset 0 so alignment/granularity rules hold.

**identifier** `qp-f4462dec57-id` (scenario; ngram 1/2, fuzz 68.5)
- Q: I call vkCmdCopyImage2: srcImage is a 2D color image created with VK_IMAGE_CREATE_SUBSAMPLED_BIT_EXT, dstImage a normal 2D image of identical format, size and sample count. Usage, format features, memory binding and TRANSFER_SRC/DST_OPTIMAL layouts are correct; one region copies all of mip 0, layer 0. What is wrong?
- A: srcImage in VkCopyImageInfo2 must not have been created with VK_IMAGE_CREATE_SUBSAMPLED_BIT_EXT in its flags, so a subsampled image cannot be the source of this copy; everything else in the setup is valid.
- notes: Destination is not subsampled; same type, format, samples; full-subresource region at offset 0 so alignment/granularity rules hold.

## VUID-VkVideoEncodeH264RateControlInfoKHR-idrPeriod-08284
- stratum `ext_niche`, entity `VkVideoEncodeH264RateControlInfoKHR` (api), assigned `yes_no`, verdict `yes`
- **VU:** If idrPeriod is not 0, then it must be greater than or equal to gopFrameCount

**descriptive** `qp-2445ff385a-de` (yes_no; ngram 0/1, fuzz 49.4)
- Q: For H.264 encode rate control, if I specify a non-zero interval between IDR frames, does that interval have to be no smaller than the number of frames in a group of pictures?
- A: Yes. In VkVideoEncodeH264RateControlInfoKHR, a non-zero idrPeriod must be greater than or equal to gopFrameCount.

**identifier** `qp-3dd3880816-id` (yes_no; ngram 0/1, fuzz 61.4)
- Q: In VkVideoEncodeH264RateControlInfoKHR, when I set idrPeriod to a non-zero value, is it required to be at least gopFrameCount?
- A: Yes. If idrPeriod is not 0, it must be greater than or equal to gopFrameCount; an idrPeriod of 0 is not subject to this constraint.

## VUID-vkCmdDrawClusterHUAWEI-None-07644
- stratum `ext_niche`, entity `vkCmdDrawClusterHUAWEI` (api), assigned `scenario`
- **VU:** If the VK_NV_framebuffer_mixed_samples extension is enabled, a shader object is bound to any graphics stage or a graphics pipeline is bound which was created with the VK_DYNAMIC_STATE_COVERAGE_MODULATION_MODE_NV dynamic state enabled, and the current value of rasterizerDiscardEnable is VK_FALSE, then vkCmdSetCoverageModulationModeNV must have been called and not subsequently invalidated in the current command buffer prior to this drawing command

**descriptive** `qp-fbf17c3600-de` (scenario; ngram 2/2, fuzz 46.4)
- Q: The extension allowing mixed color and depth sample counts is enabled. My pipeline has a cluster culling stage and a fragment stage, no descriptors, sample shading off, rasterization discard statically off, and only the coverage modulation mode left dynamic. In the matching render pass and subpass I issue one cluster draw with a 1x1x1 group count, never having set any dynamic state and with no queries running. What is wrong?
- A: The coverage modulation mode was never set: since the pipeline has VK_DYNAMIC_STATE_COVERAGE_MODULATION_MODE_NV, VK_NV_framebuffer_mixed_samples is enabled and rasterizerDiscardEnable is VK_FALSE, vkCmdSetCoverageModulationModeNV must be called and not invalidated in the command buffer before vkCmdDrawClusterHUAWEI.

**identifier** `qp-23820c200b-id` (scenario; ngram 2/3, fuzz 55.1)
- Q: VK_NV_framebuffer_mixed_samples is enabled. I bind a graphics pipeline with a ClusterCullingHUAWEI stage and a fragment stage, no descriptors, sample shading off, rasterizerDiscardEnable statically VK_FALSE, and VK_DYNAMIC_STATE_COVERAGE_MODULATION_MODE_NV as its only dynamic state. Inside the matching render pass and subpass I call vkCmdDrawClusterHUAWEI(1,1,1) without any vkCmdSet* call and with no queries active. What is wrong?
- A: Because the pipeline declares VK_DYNAMIC_STATE_COVERAGE_MODULATION_MODE_NV, the mixed-samples extension is enabled and rasterizerDiscardEnable is VK_FALSE, vkCmdSetCoverageModulationModeNV must have been called (and not invalidated) in the command buffer before the draw. Drawing without it is invalid.

## VUID-vkCmdDrawIndexedIndirect-None-08689
- stratum `ext_niche`, entity `vkCmdDrawIndexedIndirect` (api), assigned `scenario`
- **VU:** If there is no bound graphics pipeline, and the taskShader feature is enabled, vkCmdBindShadersEXT must have been called in the current command buffer with pStages with an element of VK_SHADER_STAGE_TASK_BIT_EXT

**descriptive** `qp-d7f726b98d-de` (scenario; ngram 2/2, fuzz 56.9)
- Q: I issue an indexed indirect draw using standalone shader objects and no graphics pipeline. Task and mesh shading features are enabled, tessellation and geometry shading are not. In this command buffer I bound valid vertex and fragment shaders and explicitly bound nothing (a null handle) to the mesh stage, but no bind call ever included the task stage. Is that valid?
- A: No. If no graphics pipeline is bound and the taskShader feature is enabled, vkCmdBindShadersEXT must have been called in the current command buffer with an element of pStages equal to VK_SHADER_STAGE_TASK_BIT_EXT (a null shader is acceptable). Never naming the task stage makes the vkCmdDrawIndexedIndirect invalid.
- notes: Mesh stage explicitly unbound and vertex bound so the other per-stage bind VUs and the vertex/mesh exclusivity VUs are satisfied.

**identifier** `qp-7979434efb-id` (scenario; ngram 4/4, fuzz 57.8)
- Q: I draw with vkCmdDrawIndexedIndirect using shader objects and no bound graphics pipeline. The device has shaderObject, meshShader and taskShader enabled; tessellationShader and geometryShader are disabled. In this command buffer I called vkCmdBindShadersEXT for VK_SHADER_STAGE_VERTEX_BIT and VK_SHADER_STAGE_FRAGMENT_BIT with valid shaders and for VK_SHADER_STAGE_MESH_BIT_EXT with VK_NULL_HANDLE. What is wrong?
- A: With no graphics pipeline bound and the taskShader feature enabled, vkCmdBindShadersEXT must have been called in the current command buffer with VK_SHADER_STAGE_TASK_BIT_EXT among its pStages (for example binding VK_NULL_HANDLE to it). The task stage was never included in any bind call, so the draw is invalid.
- notes: Mesh stage explicitly unbound and vertex bound so the other per-stage bind VUs and the vertex/mesh exclusivity VUs are satisfied.

## VUID-vkCmdDrawIndexedIndirect2KHR-stippledLineEnable-07496
- stratum `ext_niche`, entity `vkCmdDrawIndexedIndirect2KHR` (api), assigned `rule`
- **VU:** If the bound graphics pipeline state was created with the VK_DYNAMIC_STATE_LINE_STIPPLE_ENABLE_EXT or VK_DYNAMIC_STATE_LINE_RASTERIZATION_MODE_EXT dynamic states enabled, and if the current stippledLineEnable state is VK_TRUE and the current lineRasterizationMode state is VK_LINE_RASTERIZATION_MODE_BRESENHAM, then the stippledBresenhamLines feature must be enabled

**descriptive** `qp-ae99aeef25-de` (rule; ngram 1/2, fuzz 53.9)
- Q: In the newer address-based indexed indirect draw, my pipeline leaves line stippling on/off and the line rasterization mode as dynamic state. If I turn stippling on and pick Bresenham-style lines, what device feature has to be enabled for the draw?
- A: When the bound graphics pipeline was created with VK_DYNAMIC_STATE_LINE_STIPPLE_ENABLE_EXT or VK_DYNAMIC_STATE_LINE_RASTERIZATION_MODE_EXT as dynamic state, and at draw time stippledLineEnable is VK_TRUE with lineRasterizationMode set to VK_LINE_RASTERIZATION_MODE_BRESENHAM, the stippledBresenhamLines feature has to be enabled on the device.

**identifier** `qp-7219f374f5-id` (rule; ngram 1/1, fuzz 72.6)
- Q: My pipeline uses VK_DYNAMIC_STATE_LINE_STIPPLE_ENABLE_EXT and VK_DYNAMIC_STATE_LINE_RASTERIZATION_MODE_EXT. Before calling vkCmdDrawIndexedIndirect2KHR I set stippledLineEnable to VK_TRUE and lineRasterizationMode to VK_LINE_RASTERIZATION_MODE_BRESENHAM. Which device feature does this draw require?
- A: When the bound graphics pipeline was created with VK_DYNAMIC_STATE_LINE_STIPPLE_ENABLE_EXT or VK_DYNAMIC_STATE_LINE_RASTERIZATION_MODE_EXT as dynamic state, and at draw time stippledLineEnable is VK_TRUE with lineRasterizationMode set to VK_LINE_RASTERIZATION_MODE_BRESENHAM, the stippledBresenhamLines feature has to be enabled on the device.

## VUID-vkCmdDrawIndirect-None-02693
- stratum `ext_niche`, entity `vkCmdDrawIndirect` (api), assigned `rule`
- **VU:** If the VK_EXT_filter_cubic extension is not enabled and any VkImageView is sampled with VK_FILTER_CUBIC_EXT as a result of this command, it must not have a VkImageViewType of VK_IMAGE_VIEW_TYPE_3D, VK_IMAGE_VIEW_TYPE_CUBE, or VK_IMAGE_VIEW_TYPE_CUBE_ARRAY

**descriptive** `qp-3018db2308-de` (rule; ngram 2/1, fuzz 44.6)
- Q: I only have the older vendor-specific cubic filtering extension, not the multi-vendor one. In an indirect non-indexed draw, a shader samples an image view through a sampler set to cubic filtering. Which kinds of image views am I not permitted to sample this way?
- A: If VK_EXT_filter_cubic is not enabled, an image view sampled with VK_FILTER_CUBIC_EXT by vkCmdDrawIndirect must not have view type VK_IMAGE_VIEW_TYPE_3D, VK_IMAGE_VIEW_TYPE_CUBE or VK_IMAGE_VIEW_TYPE_CUBE_ARRAY, i.e. 3D, cube and cube array views are excluded.
- notes: Question asks for the view types forbidden outright; filterCubic query and format feature VUs are separate requirements not asked about.

**identifier** `qp-5ef7e4e937-id` (rule; ngram 2/2, fuzz 54.0)
- Q: My device supports VK_IMG_filter_cubic but I have not enabled VK_EXT_filter_cubic. If a shader invoked by vkCmdDrawIndirect samples an image view with a VK_FILTER_CUBIC_EXT sampler, which VkImageViewType values are not allowed for that view?
- A: When VK_EXT_filter_cubic is not enabled, any VkImageView sampled with VK_FILTER_CUBIC_EXT as a result of vkCmdDrawIndirect must not be of type VK_IMAGE_VIEW_TYPE_3D, VK_IMAGE_VIEW_TYPE_CUBE or VK_IMAGE_VIEW_TYPE_CUBE_ARRAY.
- notes: Question asks for the view types forbidden outright; filterCubic query and format feature VUs are separate requirements not asked about.

## VUID-vkCmdDrawMeshTasksEXT-subpass-02685
- stratum `ext_niche`, entity `vkCmdDrawMeshTasksEXT` (api), assigned `yes_no`, verdict `no`
- **VU:** The subpass index of the current render pass must be equal to the subpass member of the VkGraphicsPipelineCreateInfo structure specified when creating the VkPipeline bound to VK_PIPELINE_BIND_POINT_GRAPHICS

**descriptive** `qp-f8fcf80db1-de` (yes_no; ngram 2/2, fuzz 49.3)
- Q: My mesh-shader pipeline was built for the first subpass of a render pass, but I have already advanced to the second subpass. Can I still issue a mesh task draw with that same pipeline bound?
- A: No. When drawing with vkCmdDrawMeshTasksEXT, the index of the current subpass must equal the subpass value given in VkGraphicsPipelineCreateInfo when the bound graphics pipeline was created; a pipeline made for subpass 0 cannot draw in subpass 1.

**identifier** `qp-36faa89d82-id` (yes_no; ngram 2/2, fuzz 46.5)
- Q: I created my mesh-shading graphics pipeline with VkGraphicsPipelineCreateInfo::subpass = 0, but after vkCmdNextSubpass the render pass is now in subpass 1. Is it allowed to call vkCmdDrawMeshTasksEXT with that pipeline still bound?
- A: No. For vkCmdDrawMeshTasksEXT, the current subpass index of the render pass must equal the subpass member of the VkGraphicsPipelineCreateInfo used to create the bound graphics pipeline, so a pipeline built for subpass 0 cannot be used in subpass 1.

## VUID-vkCmdDrawMeshTasksIndirectCountNV-None-07649
- stratum `ext_niche`, entity `vkCmdDrawMeshTasksIndirectCountNV` (api), assigned `rule`
- **VU:** If the coverageReductionMode feature is enabled, a shader object is bound to any graphics stage or a graphics pipeline is bound which was created with the VK_DYNAMIC_STATE_COVERAGE_REDUCTION_MODE_NV dynamic state enabled, and the current value of rasterizerDiscardEnable is VK_FALSE, then vkCmdSetCoverageReductionModeNV must have been called and not subsequently invalidated in the current command buffer prior to this drawing command

**descriptive** `qp-551bad7584-de` (rule; ngram 2/2, fuzz 51.7)
- Q: With the coverage reduction mode feature enabled, my graphics pipeline leaves the coverage reduction mode dynamic and does not discard rasterization. Before an indirect mesh task draw that also reads its draw count from a buffer (the NVIDIA variant), what do I have to record?
- A: The command buffer must contain a prior vkCmdSetCoverageReductionModeNV call, not invalidated since, before vkCmdDrawMeshTasksIndirectCountNV when coverageReductionMode is enabled, VK_DYNAMIC_STATE_COVERAGE_REDUCTION_MODE_NV is dynamic (or a shader object is bound) and rasterizerDiscardEnable is VK_FALSE.

**identifier** `qp-d82045c0a2-id` (rule; ngram 2/3, fuzz 61.1)
- Q: The coverageReductionMode feature is on, and my bound graphics pipeline lists VK_DYNAMIC_STATE_COVERAGE_REDUCTION_MODE_NV as dynamic with rasterizer discard disabled. What state-setting call do I need to record before vkCmdDrawMeshTasksIndirectCountNV?
- A: vkCmdSetCoverageReductionModeNV must have been called earlier in the current command buffer, and not invalidated since, before vkCmdDrawMeshTasksIndirectCountNV, whenever the coverageReductionMode feature is enabled, the pipeline (or a shader object) makes coverage reduction mode dynamic, and rasterizerDiscardEnable is VK_FALSE.

## VUID-VkCopyAccelerationStructureInfoKHR-buffer-03719
- stratum `ext_popular`, entity `VkCopyAccelerationStructureInfoKHR` (api), assigned `rule`
- **VU:** The range of dst accessed by this command must be fully backed by physical memory

**descriptive** `qp-b89d185a91-de` (rule; ngram 1/1, fuzz 44.4)
- Q: When copying one acceleration structure into another, the buffer holding the target structure might be only partially bound to device memory. What must hold for the portion of the target that the copy reads or writes?
- A: The range of the destination acceleration structure (dst in VkCopyAccelerationStructureInfoKHR) accessed by the copy must be fully backed by physical memory.
- notes: Question restricted to physical backing so the size and overlap rules for dst do not apply.

**identifier** `qp-29dea1217d-id` (rule; ngram 1/1, fuzz 48.1)
- Q: I copy an acceleration structure with VkCopyAccelerationStructureInfoKHR, and the buffer behind dst may not be completely bound to device memory. What is required of the dst memory backing for the part the copy touches?
- A: Every byte of dst that the copy command accesses has to be fully backed by physical memory; unbacked regions within the accessed range of dst are not allowed.
- notes: Question restricted to physical backing so the size and overlap rules for dst do not apply.

## VUID-VkGraphicsPipelineCreateInfo-pLibraries-06611
- stratum `ext_popular`, entity `VkGraphicsPipelineCreateInfo` (api), assigned `scenario`
- **VU:** Any pipeline libraries included via VkPipelineLibraryCreateInfoKHR::pLibraries must not include any state subset already defined by this structure or defined by any other pipeline library in VkPipelineLibraryCreateInfoKHR::pLibraries

**descriptive** `qp-c19a5e8522-de` (scenario; ngram 2/2, fuzz 46.8)
- Q: With graphics pipeline libraries supported, I'm building a partial pipeline meant for later linking that itself supplies the vertex input part, with valid vertex binding and primitive topology settings, and I also link in one existing library that was built with the same creation flags and contains only its own vertex input part. What is wrong here?
- A: The library in VkPipelineLibraryCreateInfoKHR::pLibraries contains the vertex input interface state subset, but the pipeline being created already defines that subset itself via VK_GRAPHICS_PIPELINE_LIBRARY_VERTEX_INPUT_INTERFACE_BIT_EXT. A linked library must not include any state subset that this VkGraphicsPipelineCreateInfo already defines (or that another linked library defines), so this is invalid.
- notes: Scenario uses only the vertex input interface subset so the pre-rasterization/fragment matching rules (layout, subpass, render pass, multisample, viewMask) do not apply; the linked library has the same create flags, so flag-propagation rules are satisfied.

**identifier** `qp-6f890544c6-id` (scenario; ngram 1/1, fuzz 55.4)
- Q: With graphicsPipelineLibrary enabled, I call vkCreateGraphicsPipelines with flags = VK_PIPELINE_CREATE_LIBRARY_BIT_KHR, VkGraphicsPipelineLibraryCreateInfoEXT::flags = VK_GRAPHICS_PIPELINE_LIBRARY_VERTEX_INPUT_INTERFACE_BIT_EXT, valid pVertexInputState and pInputAssemblyState, and VkPipelineLibraryCreateInfoKHR::pLibraries holding one library created with the same flags and only that same library bit. What is wrong?
- A: The library in VkPipelineLibraryCreateInfoKHR::pLibraries contains the vertex input interface state subset, but the pipeline being created already defines that subset itself via VK_GRAPHICS_PIPELINE_LIBRARY_VERTEX_INPUT_INTERFACE_BIT_EXT. A linked library must not include any state subset that this VkGraphicsPipelineCreateInfo already defines (or that another linked library defines), so this is invalid.
- notes: Scenario uses only the vertex input interface subset so the pre-rasterization/fragment matching rules (layout, subpass, render pass, multisample, viewMask) do not apply; the linked library has the same create flags, so flag-propagation rules are satisfied.

## VUID-VkShaderCreateInfoEXT-stage-08420
- stratum `ext_popular`, entity `VkShaderCreateInfoEXT` (api), assigned `rule`
- **VU:** If the geometryShader feature is not enabled, stage must not be VK_SHADER_STAGE_GEOMETRY_BIT

**descriptive** `qp-11ea6a852f-de` (rule; ngram 1/1, fuzz 51.1)
- Q: I want to create a standalone shader object for the geometry stage, but the device was created without turning on geometry shader support. What is required for this to be valid?
- A: A shader object whose stage is VK_SHADER_STAGE_GEOMETRY_BIT may only be created when the geometryShader feature is enabled; without that feature, VkShaderCreateInfoEXT::stage cannot be the geometry stage.
- notes: Question is about the stage member itself; the nextStage geometry rule is a different member.

**identifier** `qp-fa30b585a6-id` (rule; ngram 1/2, fuzz 67.1)
- Q: I fill a VkShaderCreateInfoEXT with stage = VK_SHADER_STAGE_GEOMETRY_BIT to make a geometry shader object, but I did not enable the geometryShader feature on the device. What is required for this to be valid?
- A: VkShaderCreateInfoEXT::stage must not be VK_SHADER_STAGE_GEOMETRY_BIT unless the geometryShader feature is enabled; to create a geometry-stage shader object you have to enable geometryShader.
- notes: Question is about the stage member itself; the nextStage geometry rule is a different member.

## VUID-vkBuildAccelerationStructuresKHR-pInfos-03767
- stratum `ext_popular`, entity `vkBuildAccelerationStructuresKHR` (api), assigned `yes_no`, verdict `no`
- **VU:** For each element of pInfos, if its mode member is VK_BUILD_ACCELERATION_STRUCTURE_MODE_UPDATE_KHR, then for each VkAccelerationStructureGeometryKHR structure referred to by its pGeometries or ppGeometries members, if geometryType is VK_GEOMETRY_TYPE_TRIANGLES_KHR, if its geometry.triangles.transformData address was not NULL when srcAccelerationStructure was last built, then it must not be NULL

**descriptive** `qp-ae92a7674b-de` (yes_no; ngram 2/3, fuzz 50.0)
- Q: I'm updating an acceleration structure on the host. One of its triangle geometries used a transform matrix address when the source structure was last built. Is it allowed to drop the transform, passing a null address, for that geometry in the update?
- A: No. For VK_BUILD_ACCELERATION_STRUCTURE_MODE_UPDATE_KHR, a VK_GEOMETRY_TYPE_TRIANGLES_KHR geometry whose transformData was non-NULL when srcAccelerationStructure was last built must keep a non-NULL transformData in the update.

**identifier** `qp-17b357d107-id` (yes_no; ngram 2/4, fuzz 60.8)
- Q: In a host vkBuildAccelerationStructuresKHR call with mode VK_BUILD_ACCELERATION_STRUCTURE_MODE_UPDATE_KHR, one VK_GEOMETRY_TYPE_TRIANGLES_KHR geometry had a non-NULL geometry.triangles.transformData when srcAccelerationStructure was last built. Can I pass a NULL transformData for that geometry in this update?
- A: No. In an update, if a triangle geometry's geometry.triangles.transformData address was non-NULL in the last build of srcAccelerationStructure, it must be non-NULL in the update as well.

## VUID-vkCmdBuildAccelerationStructuresIndirectKHR-dstAccelerationStructure-03703
- stratum `ext_popular`, entity `vkCmdBuildAccelerationStructuresIndirectKHR` (api), assigned `scenario`
- **VU:** The range of memory backing the dstAccelerationStructure member of any element of pInfos that is accessed by this command must not overlap the memory backing the scratchData member of any element of pInfos (including the same element), which is accessed by this command

**descriptive** `qp-ac3e8c330f-de` (scenario; ngram 1/1, fuzz 47.6)
- Q: I record an indirect, device-side build of one bottom-level triangle acceleration structure. I suballocate a 2-megabyte buffer with all needed usages: the destination structure sits at offset 0 with a size of 512 kilobytes (enough), and the scratch address points to offset 256 kilobytes, correctly aligned, with the scratch range inside the buffer. Everything else is valid. What's wrong?
- A: The destination acceleration structure's memory accessed by vkCmdBuildAccelerationStructuresIndirectKHR must not overlap the scratch memory (scratchData) of any build in the call, including its own. Scratch at offset 256 KiB falls within the destination's 0-512 KiB range, so they overlap.
- notes: Single element, BUILD mode, so the other-element and source-structure overlap rules do not apply.

**identifier** `qp-601f760c90-id` (scenario; ngram 1/1, fuzz 47.8)
- Q: I record vkCmdBuildAccelerationStructuresIndirectKHR with infoCount = 1 (BUILD mode, bottom-level triangles). One 2 MiB buffer with all required usages holds dstAccelerationStructure at offset 0 with size 512 KiB (large enough), and scratchData.deviceAddress is the buffer address + 256 KiB, correctly aligned with the scratch range inside the buffer. Everything else is valid. What's wrong?
- A: The memory backing dstAccelerationStructure that the build accesses must be disjoint from the memory backing scratchData of every element of pInfos, its own element included. Scratch starting at 256 KiB lies inside the acceleration structure's 0-512 KiB range, so the two overlap.
- notes: Single element, BUILD mode, so the other-element and source-structure overlap rules do not apply.

## VUID-vkCmdDrawIndirect-attachmentCount-07750
- stratum `ext_popular`, entity `vkCmdDrawIndirect` (api), assigned `scenario`
- **VU:** If the colorWriteEnable feature is enabled, a shader object is bound to the VK_SHADER_STAGE_FRAGMENT_BIT stage or a graphics pipeline is bound which was created with the VK_DYNAMIC_STATE_COLOR_WRITE_ENABLE_EXT dynamic state enabled, and the current value of rasterizerDiscardEnable is VK_FALSE, then the attachmentCount parameter of the most recent call to vkCmdSetColorWriteEnableEXT in the current command buffer must be greater than or equal to the number of active color attachments

**descriptive** `qp-6a6f8f407a-de` (scenario; ngram 2/2, fuzz 44.9)
- Q: Per-attachment color write toggling is enabled on my device, and my pipeline sets that toggle as its only dynamic state, with rasterization not discarded. The subpass has three active color targets. I set the write toggles for just two attachments right before an indirect non-indexed draw. Is this valid?
- A: No. When the colorWriteEnable feature is enabled, the pipeline has VK_DYNAMIC_STATE_COLOR_WRITE_ENABLE_EXT and rasterizerDiscardEnable is VK_FALSE, the most recent vkCmdSetColorWriteEnableEXT call must have an attachmentCount greater than or equal to the number of active color attachments; 2 is fewer than the 3 active ones.
- notes: Only color write enable is dynamic (no dynamic write mask), render pass begun with vkCmdBeginRenderPass-compatible setup, so dynamic-rendering and write-mask VUs do not apply.

**identifier** `qp-3a4c9936fc-id` (scenario; ngram 3/4, fuzz 59.7)
- Q: The colorWriteEnable feature is enabled. My graphics pipeline's only dynamic state is VK_DYNAMIC_STATE_COLOR_WRITE_ENABLE_EXT, rasterizerDiscardEnable is VK_FALSE, and it targets a subpass with three active color attachments. Inside that render pass I call vkCmdSetColorWriteEnableEXT with attachmentCount = 2 and then vkCmdDrawIndirect. What is wrong?
- A: With colorWriteEnable enabled, a pipeline using VK_DYNAMIC_STATE_COLOR_WRITE_ENABLE_EXT and rasterizerDiscardEnable VK_FALSE, the attachmentCount of the latest vkCmdSetColorWriteEnableEXT in the command buffer must be at least the number of active color attachments. Passing 2 when three color attachments are active violates this.
- notes: Only color write enable is dynamic (no dynamic write mask), render pass begun with vkCmdBeginRenderPass-compatible setup, so dynamic-rendering and write-mask VUs do not apply.

## VUID-vkCmdDrawMultiIndexedEXT-stippledLineEnable-07495
- stratum `ext_popular`, entity `vkCmdDrawMultiIndexedEXT` (api), assigned `yes_no`, verdict `yes`
- **VU:** If the bound graphics pipeline state was created with the VK_DYNAMIC_STATE_LINE_STIPPLE_ENABLE_EXT or VK_DYNAMIC_STATE_LINE_RASTERIZATION_MODE_EXT dynamic states enabled, and if the current stippledLineEnable state is VK_TRUE and the current lineRasterizationMode state is VK_LINE_RASTERIZATION_MODE_RECTANGULAR, then the stippledRectangularLines feature must be enabled

**descriptive** `qp-8452ef6c67-de` (yes_no; ngram 1/2, fuzz 57.1)
- Q: My pipeline sets line stippling on/off and the line rasterization mode dynamically. If I enable stippling and choose rectangular lines, do I need the stippled rectangular lines device feature turned on before issuing a multi-draw of indexed geometry?
- A: Yes. When the bound pipeline was created with VK_DYNAMIC_STATE_LINE_STIPPLE_ENABLE_EXT or VK_DYNAMIC_STATE_LINE_RASTERIZATION_MODE_EXT dynamic, stippledLineEnable is VK_TRUE and lineRasterizationMode is VK_LINE_RASTERIZATION_MODE_RECTANGULAR, the stippledRectangularLines feature must be enabled for vkCmdDrawMultiIndexedEXT.

**identifier** `qp-697afaefaa-id` (yes_no; ngram 2/3, fuzz 77.9)
- Q: With a pipeline that has VK_DYNAMIC_STATE_LINE_STIPPLE_ENABLE_EXT and VK_DYNAMIC_STATE_LINE_RASTERIZATION_MODE_EXT dynamic, I set stippledLineEnable to VK_TRUE and lineRasterizationMode to VK_LINE_RASTERIZATION_MODE_RECTANGULAR. Must stippledRectangularLines be enabled to call vkCmdDrawMultiIndexedEXT?
- A: Yes. When the bound pipeline was created with VK_DYNAMIC_STATE_LINE_STIPPLE_ENABLE_EXT or VK_DYNAMIC_STATE_LINE_RASTERIZATION_MODE_EXT dynamic, stippledLineEnable is VK_TRUE and lineRasterizationMode is VK_LINE_RASTERIZATION_MODE_RECTANGULAR, the stippledRectangularLines feature must be enabled for vkCmdDrawMultiIndexedEXT.

## VUID-vkCmdTraceRaysKHR-sparseImageInt64Atomics-04474
- stratum `ext_popular`, entity `vkCmdTraceRaysKHR` (api), assigned `rule`
- **VU:** If the sparseImageInt64Atomics feature is not enabled, VkImage objects created with the VK_IMAGE_CREATE_SPARSE_RESIDENCY_BIT flag must not be accessed by atomic instructions through an OpTypeImage with a SampledType with a Width of 64 by this command

**descriptive** `qp-d98c98e2cb-de` (rule; ngram 1/2, fuzz 47.1)
- Q: In a ray tracing dispatch, my shaders run 64-bit integer atomic operations on a storage image that was created as sparse resident. If the device feature for 64-bit atomics on sparse images is off, what is the rule for this access?
- A: If the sparseImageInt64Atomics feature is not enabled, shaders invoked by vkCmdTraceRaysKHR must not perform atomic instructions through an OpTypeImage whose SampledType has Width 64 on VkImage objects created with VK_IMAGE_CREATE_SPARSE_RESIDENCY_BIT. Doing such 64-bit image atomics on sparse-resident images requires that feature.

**identifier** `qp-af30f77eb8-id` (rule; ngram 2/4, fuzz 56.4)
- Q: My ray tracing shaders, dispatched with vkCmdTraceRaysKHR, do atomics through an OpTypeImage with a 64-bit SampledType on a VkImage created with VK_IMAGE_CREATE_SPARSE_RESIDENCY_BIT. What restriction applies when sparseImageInt64Atomics is not enabled?
- A: If the sparseImageInt64Atomics feature is not enabled, shaders invoked by vkCmdTraceRaysKHR must not perform atomic instructions through an OpTypeImage whose SampledType has Width 64 on VkImage objects created with VK_IMAGE_CREATE_SPARSE_RESIDENCY_BIT. Doing such 64-bit image atomics on sparse-resident images requires that feature.

## VUID-vkCmdWriteAccelerationStructuresPropertiesKHR-accelerationStructure-08924
- stratum `ext_popular`, entity `vkCmdWriteAccelerationStructuresPropertiesKHR` (api), assigned `yes_no`, verdict `no`
- **VU:** The VkPhysicalDeviceAccelerationStructureFeaturesKHR::accelerationStructure feature must be enabled

**descriptive** `qp-31e0818803-de` (yes_no; ngram 1/1, fuzz 56.3)
- Q: Is it allowed to record the command that writes acceleration structure properties, such as compacted size, into a query pool if I never turned on the acceleration structure feature when creating the logical device?
- A: No. Recording vkCmdWriteAccelerationStructuresPropertiesKHR requires the VkPhysicalDeviceAccelerationStructureFeaturesKHR::accelerationStructure feature to be enabled on the device.

**identifier** `qp-0b31079ae7-id` (yes_no; ngram 0/0, fuzz 85.9)
- Q: Can I record vkCmdWriteAccelerationStructuresPropertiesKHR to query compacted sizes on a device where VkPhysicalDeviceAccelerationStructureFeaturesKHR::accelerationStructure was left disabled at device creation?
- A: No. vkCmdWriteAccelerationStructuresPropertiesKHR requires the VkPhysicalDeviceAccelerationStructureFeaturesKHR::accelerationStructure feature to be enabled.

## VUID-VkRenderingInfo-pColorAttachments-11515
- stratum `recent`, entity `VkRenderingInfo` (api), assigned `scenario`
- **VU:** For any element of pColorAttachments, pDepthAttachment, or pStencilAttachment, if resolveMode contains VK_RESOLVE_MODE_CUSTOM_BIT_EXT, then flags must contain VK_RENDERING_CUSTOM_RESOLVE_BIT_EXT

**descriptive** `qp-7885f8c47d-de` (scenario; ngram 1/1, fuzz 49.0)
- Q: I begin dynamic rendering with no rendering flags set, a single layer, no multiview and no depth or stencil attachment. The one color attachment is a 4x multisampled normalized color view in the color-attachment layout, resolved with the custom resolve mode into a single-sampled view of the same format and layout. Custom resolve support is enabled and the render area fits. What's wrong?
- A: When any color, depth or stencil attachment uses VK_RESOLVE_MODE_CUSTOM_BIT_EXT as its resolveMode, VkRenderingInfo::flags has to include VK_RENDERING_CUSTOM_RESOLVE_BIT_EXT. Here no flags are set, so the custom resolve flag is missing and the rendering info is invalid.
- notes: Non-integer color format allows CUSTOM resolve; flag not set so the customResolve-feature and flag-dependent rules do not apply.

**identifier** `qp-ee74934e9c-id` (scenario; ngram 1/1, fuzz 60.8)
- Q: For vkCmdBeginRendering I pass a VkRenderingInfo with flags = 0, viewMask 0, layerCount 1, no depth or stencil attachment, and one color attachment: a 4-sample UNORM view in COLOR_ATTACHMENT_OPTIMAL with resolveMode = VK_RESOLVE_MODE_CUSTOM_BIT_EXT and a single-sampled resolveImageView of the same format and layout. customResolve is enabled and renderArea fits. What's wrong?
- A: Because an attachment's resolveMode contains VK_RESOLVE_MODE_CUSTOM_BIT_EXT, VkRenderingInfo::flags has to include VK_RENDERING_CUSTOM_RESOLVE_BIT_EXT; with flags = 0 the structure is invalid. This applies to any color, depth or stencil attachment that uses the custom resolve mode.
- notes: Non-integer color format allows CUSTOM resolve; flag not set so the customResolve-feature and flag-dependent rules do not apply.

## VUID-VkResourceDescriptorInfoEXT-pNext-11401
- stratum `recent`, entity `VkResourceDescriptorInfoEXT` (api), assigned `scenario`
- **VU:** If there is a VkDebugUtilsObjectNameInfoEXT structure in the pNext chain, its objectType must be VK_OBJECT_TYPE_UNKNOWN

**descriptive** `qp-c7cc3be412-de` (scenario; ngram 1/1, fuzz 52.9)
- Q: While writing a uniform buffer descriptor into a descriptor heap, I attach a debug name structure to the descriptor info, setting the object type to buffer and leaving the handle null. The address range is valid, aligned and within limits. Is that correct?
- A: No. A VkDebugUtilsObjectNameInfoEXT chained to VkResourceDescriptorInfoEXT must have objectType set to VK_OBJECT_TYPE_UNKNOWN, not VK_OBJECT_TYPE_BUFFER.
- notes: Spec conflict: prose says use UNKNOWN with VK_NULL_HANDLE, but VkDebugUtilsObjectNameInfoEXT-objectType-02589 forbids a null handle with UNKNOWN; scenario uses BUFFER + null handle, which 02590 allows, so only 11401 is violated.

**identifier** `qp-9b90a92152-id` (scenario; ngram 1/1, fuzz 63.0)
- Q: For a VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER VkResourceDescriptorInfoEXT (valid, aligned, non-zero, in-limit range from a uniform buffer) I chain a VkDebugUtilsObjectNameInfoEXT with objectType = VK_OBJECT_TYPE_BUFFER, objectHandle = VK_NULL_HANDLE and a valid UTF-8 pObjectName. What is wrong?
- A: When a VkDebugUtilsObjectNameInfoEXT is in the pNext chain of VkResourceDescriptorInfoEXT, its objectType must be VK_OBJECT_TYPE_UNKNOWN; using VK_OBJECT_TYPE_BUFFER violates this.
- notes: Spec conflict: prose says use UNKNOWN with VK_NULL_HANDLE, but VkDebugUtilsObjectNameInfoEXT-objectType-02589 forbids a null handle with UNKNOWN; scenario uses BUFFER + null handle, which 02590 allows, so only 11401 is violated.

## VUID-vkCmdBuildAccelerationStructuresKHR-dstAccelerationStructure-11547
- stratum `recent`, entity `vkCmdBuildAccelerationStructuresKHR` (api), assigned `rule`
- **VU:** For each element of pInfos, if its type member is VK_ACCELERATION_STRUCTURE_TYPE_OPACITY_MICROMAP_KHR, its dstAccelerationStructure member must have been created with a value of VkAccelerationStructureCreateInfoKHR::type equal to either VK_ACCELERATION_STRUCTURE_TYPE_OPACITY_MICROMAP_KHR or VK_ACCELERATION_STRUCTURE_TYPE_GENERIC_KHR

**descriptive** `qp-b6a8aafaa4-de` (rule; ngram 1/2, fuzz 55.6)
- Q: I'm recording a device-side build of an opacity micromap. What type must the destination acceleration structure object have been given when I created it?
- A: For a build whose type is VK_ACCELERATION_STRUCTURE_TYPE_OPACITY_MICROMAP_KHR, the dstAccelerationStructure has to have been created with VkAccelerationStructureCreateInfoKHR::type equal to VK_ACCELERATION_STRUCTURE_TYPE_OPACITY_MICROMAP_KHR or VK_ACCELERATION_STRUCTURE_TYPE_GENERIC_KHR.

**identifier** `qp-8e43282c0a-id` (rule; ngram 1/1, fuzz 60.9)
- Q: When I build an opacity micromap with vkCmdBuildAccelerationStructuresKHR, setting pInfos[i].type to VK_ACCELERATION_STRUCTURE_TYPE_OPACITY_MICROMAP_KHR, which VkAccelerationStructureCreateInfoKHR::type values are acceptable for the object I pass as dstAccelerationStructure?
- A: If pInfos[i].type is VK_ACCELERATION_STRUCTURE_TYPE_OPACITY_MICROMAP_KHR, dstAccelerationStructure has to be an object whose VkAccelerationStructureCreateInfoKHR::type at creation was either VK_ACCELERATION_STRUCTURE_TYPE_OPACITY_MICROMAP_KHR or VK_ACCELERATION_STRUCTURE_TYPE_GENERIC_KHR.

## VUID-vkCmdBuildAccelerationStructuresKHR-micromap-11551
- stratum `recent`, entity `vkCmdBuildAccelerationStructuresKHR` (api), assigned `rule`
- **VU:** For each element of pInfos[i].pGeometries or pInfos[i].ppGeometries, if it includes a VkAccelerationStructureGeometryMicromapDataKHR structure in its pNext chain, the buffers from which the buffer device addresses for its data and triangleArray members are queried must have been created with the VK_BUFFER_USAGE_ACCELERATION_STRUCTURE_BUILD_INPUT_READ_ONLY_BIT_KHR usage flag

**descriptive** `qp-46fc588419-de` (rule; ngram 2/4, fuzz 50.4)
- Q: When recording a device build of a micromap, I supply device addresses for the micromap's raw data and for its per-triangle descriptor array. What buffer usage must the buffers those addresses come from have been created with?
- A: The buffers from which the data and triangleArray addresses of VkAccelerationStructureGeometryMicromapDataKHR are obtained need VK_BUFFER_USAGE_ACCELERATION_STRUCTURE_BUILD_INPUT_READ_ONLY_BIT_KHR in their creation usage.

**identifier** `qp-4361030744-id` (rule; ngram 2/4, fuzz 64.4)
- Q: I build a micromap with vkCmdBuildAccelerationStructuresKHR by chaining a VkAccelerationStructureGeometryMicromapDataKHR into the geometry's pNext. What usage must the buffers behind its data and triangleArray device addresses have been created with?
- A: When a geometry's pNext chain includes VkAccelerationStructureGeometryMicromapDataKHR, the buffers whose device addresses are used for its data and triangleArray members need VK_BUFFER_USAGE_ACCELERATION_STRUCTURE_BUILD_INPUT_READ_ONLY_BIT_KHR in their creation usage.

## VUID-vkCmdCopyMemoryIndirectKHR-commandBuffer-10936
- stratum `recent`, entity `vkCmdCopyMemoryIndirectKHR` (api), assigned `rule`
- **VU:** The VkCommandPool that commandBuffer was allocated from must support at least one of the queue types specified in VkPhysicalDeviceCopyMemoryIndirectPropertiesKHR::supportedQueues

**descriptive** `qp-09e74c06cd-de` (rule; ngram 1/2, fuzz 45.3)
- Q: For the indirect memory-to-memory copy command, whose copy parameters are read from device memory, which device-reported property restricts the queue family of the command pool my command buffer comes from, and what is the rule?
- A: The supportedQueues member of VkPhysicalDeviceCopyMemoryIndirectPropertiesKHR: the command pool used for vkCmdCopyMemoryIndirectKHR must support at least one of the queue types it lists.

**identifier** `qp-372fd8f17a-id` (rule; ngram 1/2, fuzz 48.2)
- Q: Beyond the generic graphics/compute/transfer requirement, what device property limits which VkCommandPool the commandBuffer for vkCmdCopyMemoryIndirectKHR may be allocated from, and how?
- A: VkPhysicalDeviceCopyMemoryIndirectPropertiesKHR::supportedQueues: the command pool of commandBuffer must support at least one of the queue types listed in supportedQueues.

## VUID-vkCmdDispatchIndirect2KHR-None-11302
- stratum `recent`, entity `vkCmdDispatchIndirect2KHR` (api), assigned `yes_no`, verdict `yes`
- **VU:** If a pipeline is bound to the pipeline bind point used by this command, or shader is bound to a shader stage used by this command, and it was created with a descriptor mapping using VK_DESCRIPTOR_MAPPING_SOURCE_PUSH_ADDRESS_EXT, and a shader accesses a resource using that mapping, the value of the address at the expected location in push data must be a valid VkDeviceAddress

**descriptive** `qp-c645753012-de` (yes_no; ngram 2/3, fuzz 53.8)
- Q: I use descriptor heaps, and one shader binding is mapped so that the resource's address is read straight out of push data. If the shader touches that resource during an address-based indirect compute dispatch, does the pushed value have to be a valid device address?
- A: Yes. For vkCmdDispatchIndirect2KHR, if the bound pipeline or shader was created with a VK_DESCRIPTOR_MAPPING_SOURCE_PUSH_ADDRESS_EXT mapping and a shader accesses a resource using it, the address at the expected push data location must be a valid VkDeviceAddress.

**identifier** `qp-d52a6bc4f3-id` (yes_no; ngram 2/3, fuzz 71.0)
- Q: My compute pipeline maps a shader binding with VK_DESCRIPTOR_MAPPING_SOURCE_PUSH_ADDRESS_EXT and the shader really accesses that resource during vkCmdDispatchIndirect2KHR. Is it required that the address stored at the expected push data location is a valid VkDeviceAddress?
- A: Yes. When the bound pipeline or shader uses a VK_DESCRIPTOR_MAPPING_SOURCE_PUSH_ADDRESS_EXT mapping and a shader accesses a resource through it, the address at the expected location in push data must be a valid VkDeviceAddress for vkCmdDispatchIndirect2KHR.

## VUID-vkCmdDrawIndexedIndirect-None-10795
- stratum `recent`, entity `vkCmdDrawIndexedIndirect` (api), assigned `yes_no`, verdict `yes`
- **VU:** If a color attachment is written by any prior command in this subpass or by the load, store, or resolve operations for this subpass, and feedback loop is not enabled for VK_IMAGE_ASPECT_COLOR_BIT on that attachment, it must not be accessed in any way other than as an attachment by this command

**descriptive** `qp-336d83f114-de` (yes_no; ngram 2/2, fuzz 48.3)
- Q: Within one subpass, a previous draw rendered into a color target, and I have not turned on the feedback loop mode for the color aspect of that target. Must my following indexed indirect draw touch that image only as a render target, rather than also reading it in a shader through a descriptor?
- A: Yes. If a color attachment was written earlier in the subpass (including by its load, store or resolve operations) and feedback loop is not enabled for VK_IMAGE_ASPECT_COLOR_BIT on it, vkCmdDrawIndexedIndirect must not access it in any way other than as an attachment.
- notes: VUID-...-None-09003 (attachment, storage image or sampled image allowed) is the weaker generic rule; the target is the stricter color-specific rule without feedback loop, so the answer is still yes.

**identifier** `qp-e806829b9e-id` (yes_no; ngram 2/3, fuzz 53.9)
- Q: An earlier draw in the current subpass wrote to a color attachment, and I left attachment feedback loop disabled for its VK_IMAGE_ASPECT_COLOR_BIT aspect. Is it required that my next vkCmdDrawIndexedIndirect use that image solely as an attachment, rather than also reading it through a descriptor in the shader?
- A: Yes. When a color attachment has been written by a prior command in the subpass (or by its load, store or resolve operations) and feedback loop is not enabled for VK_IMAGE_ASPECT_COLOR_BIT on it, vkCmdDrawIndexedIndirect must access that attachment only as an attachment.
- notes: VUID-...-None-09003 (attachment, storage image or sampled image allowed) is the weaker generic rule; the target is the stricter color-specific rule without feedback loop, so the answer is still yes.

## VUID-vkCmdDrawMultiEXT-flags-11521
- stratum `recent`, entity `vkCmdDrawMultiEXT` (api), assigned `scenario`
- **VU:** If the current render pass instance was begun with vkCmdBeginRendering with VkRenderingInfo::flags which includes VK_RENDERING_FRAGMENT_REGION_BIT_EXT, and if sample shading is enabled (explicitly or implicitly), then the minimum fraction for sample shading must equal 0.0

**descriptive** `qp-4726e63aac-de` (scenario; ngram 2/2, fuzz 48.4)
- Q: I start a dynamic rendering pass with the fragment region rendering flag set, using four-sample attachments that match my pipeline. The pipeline turns on per-sample shading with a minimum shading fraction of one half. Then I issue a multi-draw. Is that valid?
- A: No. If the render pass instance began with vkCmdBeginRendering with VK_RENDERING_FRAGMENT_REGION_BIT_EXT in VkRenderingInfo::flags and sample shading is enabled (explicitly or implicitly), the minimum fraction for sample shading must be exactly 0.0, so minSampleShading = 0.5 makes the vkCmdDrawMultiEXT invalid.
- notes: Custom-resolve VUs: the batch text does not define whether the fragment region flag alone means the pass contains a custom resolve; scenario assumes pipeline otherwise matches the render pass.

**identifier** `qp-d9c55c5d45-id` (scenario; ngram 1/1, fuzz 65.0)
- Q: I begin rendering with vkCmdBeginRendering and VkRenderingInfo::flags = VK_RENDERING_FRAGMENT_REGION_BIT_EXT, with 4-sample attachments matching the pipeline. The bound graphics pipeline has sampleShadingEnable = VK_TRUE and minSampleShading = 0.5. Then I record vkCmdDrawMultiEXT. What is wrong?
- A: When the render pass instance was begun with vkCmdBeginRendering and VkRenderingInfo::flags includes VK_RENDERING_FRAGMENT_REGION_BIT_EXT, and sample shading is enabled (explicitly or implicitly), the minimum sample shading fraction must be 0.0. A minSampleShading of 0.5 violates this.
- notes: Custom-resolve VUs: the batch text does not define whether the fragment region flag alone means the pass contains a custom resolve; scenario assumes pipeline otherwise matches the render pass.

## VUID-vkCmdDrawMultiEXT-format-10390
- stratum `recent`, entity `vkCmdDrawMultiEXT` (api), assigned `yes_no`, verdict `no`
- **VU:** For each vertex attribute accessed by this command, if its VkVertexInputAttributeDescription::format or VkVertexInputAttributeDescription2EXT::format is not a packed format, and either the legacyVertexAttributes feature is not enabled or format has 64-bit components, the value of attribAddress, calculated as described in Vertex Input Calculation, must be a multiple of the component size of the format

**descriptive** `qp-747b319746-de` (yes_no; ngram 2/2, fuzz 53.8)
- Q: On a device where the legacy vertex attribute compatibility feature is turned on, a multi-draw reads a vertex attribute in an ordinary non-packed format made of three 32-bit float components. Must the computed address of that attribute be aligned to the size of one component?
- A: No. The rule that attribAddress must be a multiple of the component size of a non-packed format applies only when legacyVertexAttributes is not enabled or the format has 64-bit components; with the feature enabled and 32-bit components (e.g. VK_FORMAT_R32G32B32_SFLOAT) it does not apply.
- notes: The packed-format rule (format-10389) does not apply since the format is not packed.

**identifier** `qp-3b8803afed-id` (yes_no; ngram 2/4, fuzz 58.6)
- Q: With the legacyVertexAttributes feature enabled, my vkCmdDrawMultiEXT reads a vertex attribute whose VkVertexInputAttributeDescription2EXT::format is VK_FORMAT_R32G32B32_SFLOAT. Must the computed attribAddress be a multiple of that format's component size?
- A: No. For a non-packed format, the requirement that attribAddress be a multiple of the component size applies only if legacyVertexAttributes is not enabled or the format has 64-bit components. With legacyVertexAttributes enabled and a 32-bit-component format such as VK_FORMAT_R32G32B32_SFLOAT, it does not apply.
- notes: The packed-format rule (format-10389) does not apply since the format is not packed.

## Unanswerable

**nonexistent** `qp-u01`
- Q: Before reusing a private data slot for a new set of objects I call vkResetPrivateDataSlot on it. Does host access to privateDataSlot have to be externally synchronized during that call, as it does for vkDestroyPrivateDataSlot?
- A: There is no such command as vkResetPrivateDataSlot in Vulkan. Values are stored per object with vkSetPrivateData, and a slot is released with vkDestroyPrivateDataSlot (whose privateDataSlot parameter must be externally synchronized); to start over you destroy the slot and create a new one.
- rationale: Invents a plausible reset command for private data slots, alongside the real create/destroy/set/get commands.
- invented: vkResetPrivateDataSlot

**nonexistent** `qp-u02`
- Q: I'm restoring a serialized micromap with vkCmdCopyMemoryToMicromapEXT using mode VK_COPY_MICROMAP_MODE_DESERIALIZE_COMPACT_EXT. Does dst then only need to be as large as the compacted size, rather than the size used when the data was serialized?
- A: There is no VK_COPY_MICROMAP_MODE_DESERIALIZE_COMPACT_EXT mode in Vulkan. For VkCopyMemoryToMicromapInfoEXT, mode must be VK_COPY_MICROMAP_MODE_DESERIALIZE_EXT, and dst must have been created with a size at least as large as the one used to serialize the data in src.
- rationale: Invents a combined deserialize+compact copy mode by merging two real VkCopyMicromapModeEXT values.
- evidence (VUID-VkCopyMemoryToMicromapInfoEXT-mode-07548): mode must be VK_COPY_MICROMAP_MODE_DESERIALIZE_EXT
- evidence (VUID-VkCopyMemoryToMicromapInfoEXT-dst-07550): dst must have been created with a size greater than or equal to that used to serialize the data in src
- invented: VK_COPY_MICROMAP_MODE_DESERIALIZE_COMPACT_EXT

**false_rule** `qp-u03`
- Q: When I fill VkAccelerationStructureCaptureDescriptorDataInfoEXT for a KHR acceleration structure, accelerationStructureNV is required to refer to the same object as accelerationStructure. What flags does that NV handle need to have been created with?
- A: The premise is false: the two members are mutually exclusive. If accelerationStructure is not VK_NULL_HANDLE, accelerationStructureNV must be VK_NULL_HANDLE (and vice versa); the KHR acceleration structure itself must have been created with VK_ACCELERATION_STRUCTURE_CREATE_DESCRIPTOR_BUFFER_CAPTURE_REPLAY_BIT_EXT in VkAccelerationStructureCreateInfoKHR::createFlags.
- rationale: Presupposes a requirement to set both handles; the spec requires the opposite.
- evidence (VUID-VkAccelerationStructureCaptureDescriptorDataInfoEXT-accelerationStructure-08093): If accelerationStructure is not VK_NULL_HANDLE then accelerationStructureNV must be VK_NULL_HANDLE
- evidence (VUID-VkAccelerationStructureCaptureDescriptorDataInfoEXT-accelerationStructure-08091): If accelerationStructure is not VK_NULL_HANDLE then accelerationStructure must have been created with VK_ACCELERATION_STRUCTURE_CREATE_DESCRIPTOR_BUFFER_CAPTURE_REPLAY_BIT_EXT set in VkAccelerationStructureCreateInfoKHR::createFlags

**false_rule** `qp-u04`
- Q: Since VkExternalFormatANDROID::externalFormat has to be nonzero whenever the structure is in a pNext chain, what nonzero value should I put there when my VkImageCreateInfo does not actually use an external format?
- A: The premise is false: externalFormat may be zero, which means no external format is used (omitting the structure is equivalent to zero). Otherwise it must be a value returned in VkAndroidHardwareBufferFormatPropertiesANDROID::externalFormat by an earlier vkGetAndroidHardwareBufferPropertiesANDROID call.
- rationale: Presupposes a nonzero requirement; the VU explicitly allows 0 and the section defines its meaning.
- evidence (VUID-VkExternalFormatANDROID-externalFormat-01894): externalFormat must be 0 or a value returned in the externalFormat member of VkAndroidHardwareBufferFormatPropertiesANDROID by an earlier call to vkGetAndroidHardwareBufferPropertiesANDROID
- evidence (VkExternalFormatANDROID): If externalFormat is zero, it indicates that no external format is used, and implementations should rely only on other format information. If this structure is not present, it is equivalent to setting externalFormat to zero.

**false_behavior** `qp-u05`
- Q: If I bind embedded immutable samplers with VkBindDescriptorBufferEmbeddedSamplersInfoEXT and set stageFlags to only VK_SHADER_STAGE_FRAGMENT_BIT, the vertex stage keeps its previous set binding. What do I need to do to bind the same set for the vertex stage too?
- A: The premise is false: stageFlags only selects pipeline bind points. Specifying a subset of a bind point's stages still affects all stages of that bind point, so VK_SHADER_STAGE_FRAGMENT_BIT alone binds the set for the whole graphics bind point, including the vertex stage, as if the original command had been called with VK_PIPELINE_BIND_POINT_GRAPHICS.
- rationale: False premise that stageFlags gives per-stage binding granularity; the section states the binding affects all stages of the bind point.
- evidence (VkBindDescriptorBufferEmbeddedSamplersInfoEXT): If stageFlags specifies a subset of all stages corresponding to one or more pipeline bind points, the binding operation still affects all stages corresponding to the given pipeline bind point(s) as if the equivalent original version of this command had been called with the same parameters.

