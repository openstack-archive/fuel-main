var Model = {}
var Collection = {}

Model.Environment = Backbone.RelationalModel.extend({
    urlRoot: '/api/environments',
    defaults: {
        name: null,
        active: false
    },
    relations: [{
        type: Backbone.HasMany,
        key: 'nodes',
        relatedModel: 'Model.Node',
        collectionType: 'Collection.Node',
        reverseRelation: {
            key: 'environment',
            includeInJSON: false
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
        return '/api/nodes'
    },
    defaults: {

    },
    relations: [{
        type: Backbone.HasMany,
        key: 'roles',
        relatedModel: 'Model.Role',
        collectionType: 'Collection.Role',
        reverseRelation: {
            key: 'node',
            includeInJSON: false
        }
    }]
});

Collection.Node = Backbone.Collection.extend({
    model: Model.Node
});

Model.Role = Backbone.RelationalModel.extend({
    urlRoot: function() {
        return this.get('node').url() + '/roles'
    }
});

Collection.Role = Backbone.Collection.extend({
    model: Model.Role
});
