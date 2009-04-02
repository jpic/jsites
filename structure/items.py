class Node(list):
    def __init__(self, name, parent=None, value=None, options={}, nodes=[]):
        for arg in nodes:
            arg.parent = self
            self.append(arg)
        self.name = name
        self.parent = parent
        self.value = value
        self.options = options

    def get_matching_values_nodes(self, **kwargs):
        matching = []
        for item in self:
            if isinstance(item, Node):
                # recurse on the node item
                matching += item.get_matching_leaves(**kwargs)
                continue

            # let match before elimination
            match = True

            # test each attribute against the current item
            for property, value in kwargs.items():
                if property in ('name', 'parent', 'value', 'options', 'nodes'):
                    test = getattr(self, property)
                else:
                    test = self.options[property]

                if not test == value:
                    match = False

            # don't append if any attribute failed to be equal
            if match:
                matching.append(item)

        return matching

    def get_matching_values_nodes_names(self, **kwargs):
        names = []
        for node in self.get_matching_values_nodes_names(**kwargs):
            names.append(node.name)
        return names

def django_model_to_node_factory(model):
    if isinstance(model, type):
        klass = model
        instance = model()
    else:
        klass = model.__class__
        instance = model

    result = Node(klass.__name__,
        value = instance.pk
        options = {
            'django_type': ('models.model'),
            'django_class': klass,
        }
    )

    for field in klass._meta.fields:
        node = Node(field.name,
            parent = result,
            value = getattr(instance, field.name, None),
            options = {
                'django_type': ('models.field',),
            },
        )
        result.append(node)

    return result

# plan
#node = registry.append(model_to_node(FooModel))
#model = registry.get_from_node("django_model", node)
