_.extend(Backbone.Model.prototype, {
  update: function(key, value, options) {
    var attrs, current;

    if (_.isArray(key)) {
      attrs = {};
      _.each(key, function(attr) {
        attrs[attr] = this.get(attr);
      }, this);
      options = value;
    } else if (_.isObject(key) || key == null) {
      attrs = key;
      options = value;
    } else {
      attrs = {};
      attrs[key] = value;
    }
    options = options ? _.clone(options) : {};

    if (this.isNew()) return false;

    // After a successful server-side save, the client is (optionally)
    // updated with the server-side state.
    var model = this;
    var success = options.success;
    options.success = function(resp, status, xhr) {
      var serverAttrs = model.parse(resp, xhr);
      if (!model.set(serverAttrs, options)) return false;
      if (success) {
        success(model, resp);
      } else {
        model.trigger('sync', model, resp, options);
      }
    };
    options.error = Backbone.wrapError(options.error, model, options);

    var partialModel = _.clone(this);
    partialModel.attributes = attrs;
    var xhr = (this.sync || Backbone.sync).call(this, 'update', partialModel, options);
    return xhr;
  }
});
