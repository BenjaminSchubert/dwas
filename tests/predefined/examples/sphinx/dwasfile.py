import dwas
import dwas.predefined

dwas.register_managed_step(dwas.predefined.sphinx(builder="html"), name="docs")
