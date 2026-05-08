"""Transfer learning tabanli duygu siniflandirma modeli."""

from tensorflow import keras
from tensorflow.keras import layers, regularizers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

from src.config import (
    FINE_TUNE_AT,
    INITIAL_LABEL_SMOOTHING,
    INPUT_SHAPE,
    LEARNING_RATE,
    NUM_CLASSES,
    PROJECT_ROOT,
)


def _get_mobilenet_weights():
    return keras.utils.get_file(
        fname="mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_96_no_top.h5",
        origin=(
            "https://storage.googleapis.com/tensorflow/keras-applications/"
            "mobilenet_v2/mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_96_no_top.h5"
        ),
        cache_dir=str(PROJECT_ROOT / ".keras"),
        cache_subdir="models",
    )


def build_baseline_model(
    input_shape=INPUT_SHAPE,
    num_classes=NUM_CLASSES,
) -> tuple[keras.Model, keras.Model]:
    augmentation = keras.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.08),
            layers.RandomTranslation(0.08, 0.08),
            layers.RandomZoom(0.1),
            layers.RandomContrast(0.1),
        ],
        name="augmentation",
    )

    base_model = MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights=_get_mobilenet_weights(),
    )
    base_model.trainable = False

    inputs = keras.Input(shape=input_shape)
    x = augmentation(inputs)
    x = preprocess_input(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.35)(x)
    x = layers.Dense(
        384,
        activation="swish",
        kernel_regularizer=regularizers.l2(1e-4),
    )(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(
        128,
        activation="swish",
        kernel_regularizer=regularizers.l2(5e-5),
    )(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name="emotion_mobilenetv2")

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss=keras.losses.CategoricalCrossentropy(label_smoothing=INITIAL_LABEL_SMOOTHING),
        metrics=["accuracy"],
    )
    return model, base_model


def unfreeze_for_fine_tuning(model: keras.Model, base_model: keras.Model) -> keras.Model:
    base_model.trainable = True

    for layer in base_model.layers[:FINE_TUNE_AT]:
        layer.trainable = False

    return model
