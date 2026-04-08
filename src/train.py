"""Model egitimi icin giris noktasi."""

import csv

from tensorflow import keras

from src.config import (
    ARTIFACTS_DIR,
    EPOCHS,
    FINE_TUNE_LEARNING_RATE,
    HISTORY_PATH,
    MODEL_PATH,
)
from src.data.data_loader import load_datasets
from src.models.build_model import build_baseline_model, unfreeze_for_fine_tuning


def build_callbacks():
    return [
        keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=5,
            restore_best_weights=True,
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=2,
            min_lr=1e-6,
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=str(MODEL_PATH),
            monitor="val_accuracy",
            save_best_only=True,
        ),
    ]


def save_history(history) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(HISTORY_PATH, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        keys = list(history.history.keys())
        writer.writerow(keys)

        for row in zip(*(history.history[key] for key in keys)):
            writer.writerow(row)


def merge_histories(*histories):
    merged_history = {}

    for history in histories:
        for key, values in history.history.items():
            merged_history.setdefault(key, []).extend(values)

    class HistoryContainer:
        def __init__(self, data):
            self.history = data

    return HistoryContainer(merged_history)


def main() -> None:
    print("Model egitimi basliyor.")

    train_dataset, validation_dataset, _, steps_per_epoch = load_datasets()
    model, base_model = build_baseline_model()

    print("\nModel ozeti:")
    model.summary()
    print(f"\nStep sayisi: {steps_per_epoch}")

    initial_epochs = max(1, EPOCHS // 2)
    fine_tune_epochs = max(1, EPOCHS - initial_epochs)

    initial_history = model.fit(
        train_dataset,
        validation_data=validation_dataset,
        epochs=initial_epochs,
        callbacks=build_callbacks(),
        steps_per_epoch=steps_per_epoch,
    )

    model = unfreeze_for_fine_tuning(model, base_model)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=FINE_TUNE_LEARNING_RATE),
        loss=keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=["accuracy"],
    )

    fine_tune_history = model.fit(
        train_dataset,
        validation_data=validation_dataset,
        epochs=initial_epochs + fine_tune_epochs,
        initial_epoch=initial_epochs,
        callbacks=build_callbacks(),
        steps_per_epoch=steps_per_epoch,
    )

    save_history(merge_histories(initial_history, fine_tune_history))
    print(f"\nEn iyi model kaydedildi: {MODEL_PATH}")
    print(f"Egitim gecmisi kaydedildi: {HISTORY_PATH}")


if __name__ == "__main__":
    main()
