from sphinx.writers.html import SmartyPantsHTMLTranslator
from sphinx.builders.html import StandaloneHTMLBuilder

class PxTranslator(SmartyPantsHTMLTranslator):
    """Adjust the HTML translator into a .px translator.
    
    """

    def visit_section(self, node):
        self.body.append("<!-- PX( -->")
        SmartyPantsHTMLTranslator.visit_section(self, node)
        self.body.append("<!-- ) -->")

class PxBuilder(StandaloneHTMLBuilder):
    def get_target_uri(self, docname, typ=None):
        import pdb;pdb.set_trace() 
        return docname + self.link_suffix
    