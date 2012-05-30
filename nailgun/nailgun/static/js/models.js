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
    urlRoot: '/api/nodes',
    defaults: {
        name: null,
        status: null,
        metadata: null
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

Model.Cookbook = Backbone.RelationalModel.extend({
    urlRoot: '/api/cookbooks',
    defaults: {
        name: null,
        version: null
    },
    relations: [{
        type: Backbone.HasMany,
        key: 'roles',
        relatedModel: 'Model.Role',
        collectionType: 'Collection.Role',
        reverseRelation: {
            key: 'cookbook',
            includeInJSON: false
        }
    }]
});

Collection.Cookbook = Backbone.Collection.extend({
    model: Model.Cookbook
});

Model.Role = Backbone.RelationalModel.extend({
    urlRoot: '/api/roles',
    defaults: {
        name: null
    }
});

Collection.Role = Backbone.Collection.extend({
    model: Model.Role
});
