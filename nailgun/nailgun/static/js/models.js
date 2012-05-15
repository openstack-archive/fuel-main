var Model = {}
var Collection = {}

Model.Environment = Backbone.RelationalModel.extend({
    urlRoot: '/api/environments',
    defaults: {
        name: null
    },
    relations: [{
        type: Backbone.HasMany,
        key: 'nodes',
        relatedModel: 'Model.Node',
        collectionType: 'Collection.Node',
        reverseRelation: {
            key: 'environment'
        }
    }]
});

Collection.Environment = Backbone.Collection.extend({
    model: Model.Environment,
    url: '/api/environments'
});


Model.Node = Backbone.RelationalModel.extend({
    idAttribute: 'name',
    urlRoot: function() {
        return this.get('environment').url() + '/nodes'
    }
});

Collection.Node = Backbone.Collection.extend({
    model: Model.Node
});