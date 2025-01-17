import numpy as np
import pandas as pd
from pydantic import BaseModel, field_validator

from schema.data_schema import TextClassificationSchema


def get_data_validator(schema: TextClassificationSchema, is_train: bool) -> BaseModel:
    """
    Returns a dynamic Pydantic data validator class based on the provided schema.

    The resulting validator checks the following:

    1. That the input DataFrame contains the ID field specified in the schema.
    2. That the data under ID field is unique.
    3. If `is_train` is `True`, that the input DataFrame contains the target field
        specified in the schema.
    4. If `is_train` is `True`, that all classes defined in the schema are present in
       the target column of the DataFrame.
    5. If `is_train` is `True`, that only the target classes specified in the
       schema are present in the target column in training data.
    6. That the input DataFrame contains the text field

    If any of these checks fail, the validator will raise a ValueError.

    Args:
        schema (TextClassificationSchema): An instance of
                                                TextClassificationSchema.
        is_train (bool): Whether the data is for training or not. Determines whether
            the presence of a target field is required in the data.

    Returns:
        BaseModel: A dynamic Pydantic BaseModel class for data validation.
    """

    class DataValidator(BaseModel):
        data: pd.DataFrame

        class Config:
            arbitrary_types_allowed = True

        @field_validator("data")
        def validate_dataframe(cls, data):

            if schema.id not in data.columns:
                raise ValueError(
                    f"ID field '{schema.id}' is not present in the given data"
                )

            if data[schema.id].duplicated().any():
                raise ValueError(
                    f"ID field '{schema.id}' does not contain unique values"
                )

            if is_train:
                if schema.target not in data.columns:
                    raise ValueError(
                        f"Target field '{schema.target}' is not present "
                        "in the given data"
                    )

                unique_target_values = set(data[schema.target].astype(str).unique())
                missing_classes = set(schema.target_classes) - unique_target_values
                if missing_classes:
                    raise ValueError(
                        "Target column in the train data does not contain all classes"
                        f" defined in the schema. Missing classes: {missing_classes}"
                    )

                for unique_val in unique_target_values:
                    if unique_val not in schema.target_classes:
                        raise ValueError(
                            f"Unexpected class '{unique_val}' in the target field. "
                            f"Expected target classes are {schema.target_classes}."
                        )

            if schema.text_field not in data.columns:
                raise ValueError(
                    f"Text field '{schema.textField}' is not present "
                    "in the given data"
                )

            return data

    return DataValidator


def validate_data(
    data: pd.DataFrame, data_schema: TextClassificationSchema, is_train: bool
) -> pd.DataFrame:
    """
    Validates the data using the provided schema.

    Args:
        data (pd.DataFrame): The train or test data to validate.
        data_schema (TextClassificationSchema): An instance of
            inaryClassificationSchema.
        is_train (bool): Whether the data is for training or not.

    Returns:
        pd.DataFrame: The validated data.
    """
    DataValidator = get_data_validator(data_schema, is_train)
    try:
        validated_data = DataValidator(data=data)
        return validated_data.data
    except ValueError as exc:
        raise ValueError(f"Data validation failed: {str(exc)}") from exc
