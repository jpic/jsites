from jpic.resources.node import ResourceNode

class ContentNode(ResourceNode):
    """
    In addition to the basic registry of resource.Node, it maintains a registry
    with relations between content classes and resources.
    """
    
    def __init__(self, **kwargs):
        self._model_class_registry = {} # model_class -> resource instance
        super(ResourceNode, self).__init__(**kwargs)

    @classmethod
    def factory(self, app_name, **kwargs):
        if not 'urlname' in kwargs:
            kwargs['urlname'] = app_name
        node = self.instanciate(**kwargs)
        node.register_app(app_name)
        return node

    def register_app(self, app_name, **kwargs):
        """
        Ugly shortcut to get started visiting your app.
        """
        from django.db.models import get_app, get_models
        app = get_app(app_name)
        for model_class in get_models(app):
            self.register_named_crud(model_class)

    def register_named_crud(self, model_class, **kwargs):
        """
        Ugly shortcut to get started visiting your actions.
        """
        crud = ModelFormResource
        object = crud(model_class=model_class, parent=self, **kwargs)
        self.register(object)

    def unregister_resource_for_model_class(self, model_class):
        resource = self._model_class_registry[model_class]
        del self._model_class_registry[model_class]
        del self._registry[resource.urlname]

    def get_resource_classes_for_model_class(self, model_class):
        """
        The trick allowing to use several resources per model: use two registries.
        """
        if not model_class in self._model_class_registry:
            raise Exception('No resources registered for model_class' % model_class)

        return self._model_class_registry[model_class].__class__

    def get_resources_for_model_class(self, model_class):
        """
        The trick allowing to use several resources per model: use two registries.
        """
        if not model_class in self._model_class_registry:
            raise Exception('No resources registered for model_class' % model_class)

        return self._model_class_registry[model_class]

    def register(self, resource):
        super(ContentNode, self).register(resource)
        
        if resource._has('model_class'):
            self._model_class_registry[resource.model_class] = resource
