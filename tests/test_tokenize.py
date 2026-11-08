from vkrag.index.tokenize import content_words, is_identifier, max_common_ngram, split_identifier, tokenize


def test_command_identifier():
    toks = tokenize("Call vkCmdBindPipeline here", stem=False)
    assert toks == ["call", "vkcmdbindpipeline", "cmd", "bind", "pipeline"]


def test_alias_command_keeps_suffix_part():
    assert split_identifier("vkCmdBeginRenderingKHR") == ["cmd", "begin", "rendering", "khr"]


def test_snake_enum():
    toks = tokenize("layout VK_IMAGE_LAYOUT_GENERAL", stem=False)
    assert toks == ["layout", "vk_image_layout_general", "image", "layout", "general"]


def test_struct_with_version_digits():
    assert split_identifier("VkPhysicalDeviceVulkan13Features") == ["physical", "device", "vulkan", "13", "features"]


def test_version_number_single_token():
    assert "1.3" in tokenize("Vulkan 1.3 or later")


def test_identifier_not_stemmed_but_parts_stemmed():
    toks = tokenize("pColorAttachments images")
    assert "pcolorattachments" in toks  # whole identifier, unstemmed
    assert "attach" in toks  # part, stemmed
    assert "imag" in toks  # plain word, stemmed


def test_stopwords_removed_but_rule_words_kept():
    toks = tokenize("the buffer must not be bound", stem=False)
    assert toks == ["buffer", "must", "not", "bound"]


def test_is_identifier():
    assert is_identifier("vkCmdDraw") and is_identifier("VK_NULL_HANDLE") and is_identifier("srcImage")
    assert is_identifier("VkBuffer")
    assert not is_identifier("buffer") and not is_identifier("Buffer") and not is_identifier("SPIR")


def test_content_words_drop_identifiers():
    assert content_words("If srcImage is a VkImage then it must be valid") == ["must", "valid"]


def test_max_common_ngram():
    a = "the image must have been created with the usage flag".split()
    b = "an image which must have been created with care".split()
    assert max_common_ngram(a, b) == 5
    assert max_common_ngram([], b) == 0
