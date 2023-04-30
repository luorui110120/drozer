from ..base import Module

class Filters(Module):
    """
    Utility methods for filtering collections of ReflectedTypes.
    """

    def match_filter(self, collection, key, term):
        """
        Implements a filter for items in collection, where the value of the
        property 'key' is equal to 'term'.
        """

        if collection.__eq__(None):
            collection = []
            
        if term.__ne__(None) and term != "":
            return [e for e in collection if str(getattr(e, key)).upper().find(str(term).upper()) >= 0]
        else:
            return collection
