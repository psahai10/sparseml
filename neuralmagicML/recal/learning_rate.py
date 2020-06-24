"""
Code related to learning rate controls that are shared across frameworks.
"""
from typing import Dict, Tuple
from neuralmagicML.recal.modifier import ModifierProp, BaseObject


class SetLearningRate(BaseObject):
    """
    Generic implementation for SetLearningRate shared across framework implementations.

    :param learning_rate: The learning rate to use once this modifier starts
    """

    def __init__(self, learning_rate: float, **kwargs):
        super().__init__(**kwargs)
        self._learning_rate = learning_rate
        self.validate_learning_rate()

    @ModifierProp()
    def learning_rate(self) -> float:
        """
        :return: The learning rate to use once this modifier starts
        """
        return self._learning_rate

    @learning_rate.setter
    def learning_rate(self, value: str):
        """
        :param value: The learning rate to use once this modifier starts
        """
        self._learning_rate = value
        self.validate_learning_rate()

    def validate_learning_rate(self):
        if self._learning_rate <= 0.0:
            raise ValueError("learning_rate must be greater than 0")

        if self._learning_rate > 1.0:
            raise ValueError("learning_rate must be less than or equal to 1.0")


class LearningRate(BaseObject):
    """
    Generic implementation for LearningRate shared across framework implementations.

    :param lr_class: The name of the lr scheduler class to use:
        [StepLR, MultiStepLR, ExponentialLR, CosineAnnealingWarmRestarts]
    :param lr_kwargs: The dictionary of keyword arguments to pass to the constructor
        for the lr_class
    :param init_lr: The initial learning rate to use once this modifier starts
    """

    def __init__(self, lr_class: str, lr_kwargs: Dict, init_lr: float, **kwargs):
        super().__init__(**kwargs)
        self._lr_class = lr_class
        self._lr_kwargs = lr_kwargs
        self._init_lr = init_lr
        self.validate_lr_info()

    @ModifierProp()
    def lr_class(self) -> str:
        """
        :return: The name of the lr scheduler class to use:
            [StepLR, MultiStepLR, ExponentialLR]
        """
        return self._lr_class

    @lr_class.setter
    def lr_class(self, value: str):
        """
        :param value: The name of the lr scheduler class to use:
            [StepLR, MultiStepLR, ExponentialLR]
        """
        self._lr_class = value
        self.validate_lr_info()

    @ModifierProp()
    def lr_kwargs(self) -> Dict:
        """
        :return: The dictionary of keyword arguments to pass to the constructor
            for the lr_class
        """
        return self._lr_kwargs

    @lr_kwargs.setter
    def lr_kwargs(self, value: Dict):
        """
        :param value: The dictionary of keyword arguments to pass to the constructor
            for the lr_class
        """
        self._lr_kwargs = value
        self.validate_lr_info()

    @ModifierProp()
    def init_lr(self) -> float:
        """
        :return: The initial learning rate to use once this modifier starts
        """
        return self._init_lr

    @init_lr.setter
    def init_lr(self, value: float):
        """
        :param value: The initial learning rate to use once this modifier starts
        """
        self._init_lr = value
        self.validate_lr_info()

    def validate_lr_info(self):
        """
        Validate the values of the params for the current instance are valid
        """

        if self._lr_class == "ExponentialLR":
            self._lr_kwargs["step_size"] = 1.0
            self._lr_class = "StepLR"

        if self._lr_class == "StepLR":
            if "gamma" not in self._lr_kwargs:
                raise ValueError("gamma must be in lr_kwargs for StepLR")
            if "step_size" not in self._lr_kwargs:
                raise ValueError("step_size must be in lr_kwargs for StepLR")
        elif self._lr_class == "MultiStepLR":
            if "gamma" not in self._lr_kwargs:
                raise ValueError("gamma must be in lr_kwargs for MultiStepLR")
            if "milestones" not in self._lr_kwargs:
                raise ValueError("milestones must be in lr_kwargs for MultiStepLR")
        elif self._lr_class == "CosineAnnealingWarmRestarts":
            if "lr_min" not in self._lr_kwargs:
                raise ValueError(
                    "lr_min must be in lr_kwargs for CosineAnnealingWarmRestarts"
                )
            if "cycle_epochs" not in self._lr_kwargs:
                raise ValueError(
                    "cycle_epochs must be in lr_kwargs for CosineAnnealingWarmRestarts"
                )
        else:
            raise ValueError("unknown lr_class given of {}".format(self._lr_class))

        if self._init_lr <= 0.0:
            raise ValueError("init_lr must be greater than 0")

        if self._init_lr > 1.0:
            raise ValueError("init_lr must be less than or equal to 1.0")

    def corrected_lr_info(
        self, steps_per_epoch: int, start_epoch: float, end_epoch: float
    ) -> Tuple[str, Dict]:
        """
        Get the corrected learning rate info for use with modifiers.
        Normalizes any epoch values to steps.

        :param steps_per_epoch: number of steps taken within each epoch
        :param start_epoch: The epoch the LR should start being controlled at
        :param end_epoch: The epoch the LR should stop being controlled at
        :return: a tuple containing the corrected lr class and keyword args
        """
        lr_class = self._lr_class
        lr_kwargs = {key: val for key, val in self._lr_kwargs.items()}

        if lr_class == "ExponentialLR":
            lr_kwargs["step_size"] = 1.0
            lr_class = "StepLR"

        if lr_class == "StepLR":
            lr_kwargs["step_size"] = round(lr_kwargs["step_size"] * steps_per_epoch)
        elif lr_class == "MultiStepLR":
            lr_kwargs["milestones"] = [
                round((mile - start_epoch) * steps_per_epoch)
                for mile in lr_kwargs["milestones"]
            ]

            for mile in self._lr_kwargs["milestones"]:
                if mile <= start_epoch:
                    raise ValueError(
                        "milestones {} all must be greater than start_epoch {}".format(
                            self._lr_kwargs["milestones"], start_epoch
                        )
                    )
                if mile >= end_epoch and end_epoch >= 0.0:
                    raise ValueError(
                        "milestones {} all must be less than end_epoch {}".format(
                            self._lr_kwargs["milestones"], end_epoch
                        )
                    )
        elif lr_class == "CosineAnnealingWarmRestarts":
            lr_kwargs["eta_min"] = lr_kwargs["lr_min"]
            del lr_kwargs["lr_min"]
            lr_kwargs["T_0"] = lr_kwargs["cycle_epochs"]
            del lr_kwargs["cycle_epochs"]
        else:
            raise ValueError("unrecognized lr_class given of {}".format(lr_class))

        return lr_class, lr_kwargs
