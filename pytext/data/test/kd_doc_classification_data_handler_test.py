#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest

from pytext.config.field_config import FeatureConfig
from pytext.config.kd_doc_classification import ModelInputConfig, Target, TargetConfig
from pytext.data import KDDocClassificationDataHandler
from pytext.data.featurizer import SimpleFeaturizer
from pytext.data.kd_doc_classification_data_handler import ModelInput, RawData
from pytext.utils.test_utils import import_tests_module


tests_module = import_tests_module()


class KDDocClassificationDataHandlerTest(unittest.TestCase):
    def setUp(self):
        file_name = tests_module.test_file("knowledge_distillation_test_tiny.tsv")
        label_config_dict = {"target_prob": True}
        data_handler_dict = {
            "columns_to_read": [
                "text",
                "target_probs",
                "target_logits",
                "target_labels",
                "doc_label",
            ]
        }
        self.data_handler = KDDocClassificationDataHandler.from_config(
            KDDocClassificationDataHandler.Config(**data_handler_dict),
            ModelInputConfig(),
            TargetConfig(**label_config_dict),
            featurizer=SimpleFeaturizer.from_config(
                SimpleFeaturizer.Config(), FeatureConfig()
            ),
        )
        self.data = self.data_handler.read_from_file(
            file_name, self.data_handler.raw_columns
        )

    def test_create_from_config(self):
        expected_columns = [
            RawData.TEXT,
            RawData.TARGET_PROBS,
            RawData.TARGET_LOGITS,
            RawData.TARGET_LABELS,
            RawData.DOC_LABEL,
        ]
        # check that the list of columns is as expected
        self.assertTrue(self.data_handler.raw_columns == expected_columns)

    def test_read_from_file(self):
        # Check if the data has 10 rows and 5 columns
        self.assertEqual(len(self.data), 10)
        self.assertEqual(len(self.data[0]), 5)

        self.assertEqual(self.data[0][RawData.TEXT], "Who R U ?")
        self.assertEqual(
            self.data[0][RawData.TARGET_PROBS],
            "[-0.005602254066616297, -5.430975914001465]",
        )
        self.assertEqual(
            self.data[0][RawData.TARGET_LABELS], '["cu:other", "cu:ask_Location"]'
        )

    def test_tokenization(self):
        data = list(self.data_handler.preprocess(self.data))

        # test tokenization without language-specific tokenizers
        self.assertListEqual(data[0][ModelInput.WORD_FEAT], ["who", "r", "u", "?"])
        self.assertListEqual(
            data[0][Target.TARGET_PROB_FIELD],
            [-0.005602254066616297, -5.430975914001465],
        )

    def test_align_target_label(self):
        target = [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]
        label_list = ["l1", "l2", "l3"]
        batch_label_list = [["l3", "l2", "l1"], ["l1", "l3", "l2"]]
        align_target = self.data_handler._align_target_label(
            target, label_list, batch_label_list
        )
        self.assertListEqual(align_target, [[0.3, 0.2, 0.1], [0.1, 0.3, 0.2]])
