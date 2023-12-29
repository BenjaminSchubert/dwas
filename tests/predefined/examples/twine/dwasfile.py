import dwas
from dwas.predefined import package, twine

dwas.register_managed_step(
    package(isolate=False),
    dependencies=["build", "wheel", "setuptools"],
)
dwas.register_managed_step(twine(), requires=["package"])
