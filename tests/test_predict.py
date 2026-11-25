import unittest
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image

from homtech.ml.predict import ExpressionAnalyzer, FaceDetector, FaceNotFound, ImageInputError, MULTIPLE_FACES
from homtech.ml.rafdb import CLASSES


class ClosePortraitTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new("RGB", (100, 100))
        self.analyzer = object.__new__(ExpressionAnalyzer)
        self.analyzer.aligned_model_path = "aligned.joblib"
        self.analyzer.detector = Mock()

    def test_unrecognized_image_has_no_close_portrait_detection(self):
        self.assertIsNone(FaceDetector().find_close_portrait(self.image))

    def test_multiple_face_error_does_not_try_the_close_portrait_route(self):
        self.analyzer.predict = Mock(side_effect=ImageInputError(MULTIPLE_FACES))
        with self.assertRaisesRegex(ImageInputError, "Birden fazla yüz"):
            self.analyzer.predict_photo(self.image)
        self.analyzer.detector.find_close_portrait.assert_not_called()

    def test_tightly_cropped_upload_uses_the_original_portrait_for_prediction(self):
        bounds = (0.05, 0.05, 0.90, 0.90)
        self.analyzer.detector.extract.return_value = (Image.new("L", (100, 100)), bounds)
        self.analyzer.aligned_model_path = Mock()
        self.analyzer.aligned_model_path.is_file.return_value = True
        self.analyzer._predict_portrait = Mock()
        self.assertIs(self.analyzer.predict_photo(self.image), self.analyzer._predict_portrait.return_value)
        self.analyzer._predict_portrait.assert_called_once_with(self.image, bounds)

    def test_recovered_portrait_prediction_is_always_tentative(self):
        self.analyzer.predict = Mock(side_effect=FaceNotFound("Yüz bulunamadı"))
        bounds = (0.1, 0.1, 0.8, 0.8)
        self.analyzer.detector.find_close_portrait.return_value = bounds
        estimator = Mock()
        estimator.classes_ = np.arange(len(CLASSES))
        estimator.decision_function.return_value = np.array([[0, 1, 2, 5, 3, 4, 6]])
        with patch("homtech.ml.predict.load_model", return_value={"estimator": estimator, "feature_config": {}}), \
                patch("homtech.ml.predict.extract_image_features", return_value=np.zeros(10)) as features:
            result = self.analyzer.predict_photo(self.image)
        self.assertEqual(result.label, "neutral")
        self.assertEqual(result.second_label, "happy")
        self.assertEqual(result.face, bounds)
        self.assertTrue(result.uncertain)
        self.assertTrue(result.close_portrait)
        self.assertIs(features.call_args.args[0], self.image)


if __name__ == "__main__":
    unittest.main()
