odoo.define('fit_saltedge_sync_bank_statements.board', function(require) {
  "use strict";

  var core = require('web.core');
  var KanbanView = require('web_kanban.KanbanView');

  var MyBoard = KanbanView.extend({
    render: function() {
        alert('tnerder');
      this._super.apply(this, arguments);
      this.$el.sortable('option', 'disabled', true);
      this.$('.o_kanban_header').css('cursor', 'auto');
    }
  });

    core.action_registry.add('fit_saltedge_sync_bank_statements.board', MyBoard);
  return MyBoard;
});

odoo.define('fit_saltedge_sync_bank_statements_old', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var bus = require('bus.bus')
    var WebClient = require('web.WebClient');

    WebClient.include({
        init: function(parent, client_options){
            console.log('init');
            this._super(parent, client_options);
//            this.known_bus_channels = [];
//            this.known_bus_events = [];
        },
        show_application: function() {
//            var self = this;
//            console.log('show application');
//            this._super();
//            this.start_polling();
        },
    });

//    var SaltEdgeWidget = Widget.extend({
//        className: 'fit_saltedge_synchronise',
//        template: "SaltEdgeWidget",
//        init: function(parent) {
//            this._super(parent);
//            console.log('123');
//        },
//    });
//
//    core.action_registry.add('saltedge.synchronise', SaltEdgeWidget);
//
//    var SaltEdgeConnectFrame = form.AbstractField.extend({
//        init: function(parent) {
//            this._super(parent);
//            console.log('asdasdasdsadasdasdasd!!!!!!!!!!!')
////            this._super.apply(this, arguments);
////            this.set("value", "");
//        },
//        start: function() {
////            this.on("change:effective_readonly", this, function() {
////                this.display_field();
////                this.render_value();
////            });
////            this.display_field();
//            return this._super();
//        },
//        display_field: function() {
////            var self = this;
////            this.$el.html(core.qweb.render("FieldChar2", {widget: this}));
////            if (! this.get("effective_readonly")) {
////                this.$("input").change(function() {
////                    self.internal_set_value(self.$("input").val());
////                });
////            }
//        },
//        render_value: function() {
////            if (this.get("effective_readonly")) {
////                this.$el.text(this.get("value"));
////            } else {
////                this.$("input").val(this.get("value"));
////            }
//        },
//    });
//
//    core.form_widget_registry.add('SaltEdgeConnectFrame', 'fit_saltedge_sync_bank_statements.SaltEdgeConnectFrame');
});

odoo.define('fit_saltedge_sync_bank_statements', function (require) {
    "use strict";

});