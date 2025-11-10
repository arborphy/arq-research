import pytest
import relationalai.semantics as rai

from kg.model import define_arq, ARQModel


@pytest.fixture(scope="session")
def arq() -> ARQModel:
    return define_arq(rai.Model(f"arq_test"))
