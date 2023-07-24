from typing import Final

from utils.pipelines import Pipeline

from .pipes import (
    BaseOrderPipe,
    ConfirmOrderPipe,
    VerifyDocumentsPipe,
    CheckingExistsDocumentsPipe,
)
from .dto import PipeOrderDTO
from .stages import OrderProcessStage


class OrderPipelineBuilder:
    """
    Билдер пайплайна для обработки заказа.

    Позволяет собрать пайплайн для обработки заказа, начиная с
    указанного шага пайплайна.

    Например, если мы знаем, что документы есть, мы можем начать
    сразу с проверки документов и далее по пайплайну.
    Или если мы знаем, что проверка была пройдена, можем сразу
    перейти к последнему шагу - подтверждению.
    """

    # Этапы расположены в порядке их выполнения.
    _ORDER_PIPE_MAP: Final[dict[OrderProcessStage, BaseOrderPipe]] = {
        OrderProcessStage.CHECKING_EXISTS_DOCUMENTS: CheckingExistsDocumentsPipe(),
        OrderProcessStage.VERIFY_DOCUMENTS: VerifyDocumentsPipe(),
        OrderProcessStage.CONFIRM_ORDER: ConfirmOrderPipe(),
    }

    def __init__(self, start_stage: OrderProcessStage) -> None:
        """
        Инициализатор класса.

        :param start_stage: С какой стадии начинать строить пайплайн.
        """

        assert start_stage in self._ORDER_PIPE_MAP, (
            f'Стадии {start_stage} обработки заказа не существует'
        )

        self.__start_stage = start_stage

    def build(self) -> Pipeline[PipeOrderDTO]:
        """Сборка пайплайна для заказов"""

        pipeline = Pipeline[PipeOrderDTO]()
        start_stage_passed = False

        # Сборка пайплайна, начиная с указанного шага.
        for stage, pipe in self._ORDER_PIPE_MAP.items():
            if self.__start_stage == stage:
                start_stage_passed = True

            if start_stage_passed:
                pipeline.pipe(pipe)

        return pipeline
