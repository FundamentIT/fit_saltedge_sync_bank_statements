odoo.define('fit_saltedge_sync_bank_statements', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var bus = require('bus.bus');
    var core = require('web.core');
    var data = require('web.data');
    var FormView = require('web.FormView');
    var Model = require('web.DataModel');
    var WebClient = require('web.WebClient');
    var Widget = require('web.Widget');
    var _t = core._t;

    WebClient.include({
        init: function(parent, client_options){
            this._super(parent, client_options);
            this.known_bus_channels = [];
            this.known_bus_events = [];
        },
        show_application: function() {
            this.start_polling();
            return this._super();
        },
        on_logout: function() {
            var self = this;
            bus.off('notification', this, this.bus_notification);
            _(this.known_bus_channels).each(function (channel) {
                openerp.bus.bus.delete_channel(channel);
            });
            _(this.known_bus_events).each(function(e) {
                self.bus_off(e[0], e[1]);
            });
            this._super();
        },
        start_polling: function() {
            console.log('start_polling');
            this.declare_bus_channel();

            bus.bus.on('notification', this, this.bus_notification);
            bus.bus.start_polling();
        },
        bus_notification: function(notification) {
            console.log('bus notification: '+notification);
            var channel = notification[0][0];
            if (this.known_bus_channels.indexOf(channel) != -1) {
                var message = notification[0][1];
                bus.bus.trigger(channel, message);
            }
        },
        bus_on: function(eventname, eventfunction) {
            console.log(eventname, eventfunction)

            bus.bus.on(eventname, this, eventfunction);
            this.known_bus_events.push([eventname, eventfunction]);
        },
        bus_off: function(eventname, eventfunction) {

            bus.bus.on(eventname, this, eventfunction);
            var index = _.indexOf(this.known_bus_events, (eventname, eventfunction));
            this.known_bus_events.splice(index, 1);
        },
        declare_bus_channel: function() {
            console.log('declare_bus_channel');
            var self = this,
                channel = "auto_refresh";
            this.bus_on(channel, function(message) {            // generic auto referesh
                console.log('declare_bus_channel bus_on: '+message);
                var active_view = this.action_manager.inner_widget.active_view
                if (typeof(active_view) != 'undefined'){   // in mail inbox page, no active view defined
                    var controller = this.action_manager.inner_widget.active_view.controller
                    var action = this.action_manager.inner_widget.action
                    var menu = this.menu
                    if ( action.auto_search && controller.model == message  && ! controller.$buttons.hasClass('oe_editing')){
                        if (active_view.type == "kanban")
                            controller.do_reload();    // kanban view has reload function, but only do_reload works as expected
                        if (active_view.type == "list")
                            controller.reload();     // list view only has reload
                        if (active_view.type == "form")
                            menu.do_reload();
                            controller.reload();     // form view reload
                    }
                    if (message == "ir.ui.menu") {
//                        menu.do_reload_needaction();
                        menu.do_reload();
                    }
                }
            });
			this.add_bus_channel(channel);
        },
        add_bus_channel: function(channel) {
            if (this.known_bus_channels.indexOf(channel) == -1) {
                bus.bus.add_channel(channel);
                this.known_bus_channels.push(channel);
            }
        },
    });

    FormView.include({
        is_action_enabled: function(action) {
            if (this.model == "fit.saltedge.synchronise" && this.datarecord && this.datarecord.state == "noEditable" &&
                (action == 'delete' || action == 'edit')) {
                // don't allow edit nor delete
                return false;
            }
            // call default is_action_enabled method
            return this._super.apply(this, arguments);
        },
        deleteItem: null,
        deleteItemIdx: null,
        deleteItemShown: true,
        reinit_actions: function() {
            // apply for my custom model only
            if (this.model == "fit.saltedge.synchronise") {
                // hide/show edit button
                if (this.is_action_enabled('edit')) {
                    this.$buttons.find(".o_form_button_edit").show();
                } else {
                    this.$buttons.find(".o_form_button_edit").hide();
                }

                // find delete item in sidebar's items
                if (!this.deleteItem) {
                    // form view is adding it to "other"
                    if (this.sidebar && this.sidebar.items && this.sidebar.items.other) {
                        for (var i = 0; i < this.sidebar.items.other.length; i++) {
                            // on_button_delete is used as callback for delete button
                            // it's ugly way to find out which one is delete button, haven't found better way
                            if (this.sidebar.items.other[i].callback == this.on_button_delete) {
                                this.deleteItem = this.sidebar.items.other[i];
                                this.deleteItemIdx = i;
                                break;
                            }
                        }
                    }
                }
                // hide/show delete button
                if (this.is_action_enabled('delete')) {
                    if (!this.deleteItemShown) {
                        this.deleteItemShown = true;
                        // add delete item to sidebar's items
                        this.sidebar.items.other.splice(this.deleteItemIdx, 0, this.deleteItem);
                    }
                } else
                if (this.deleteItemShown) {
                    this.deleteItemShown = false;
                    // remove delete item from sidebar's items
                    this.sidebar.items.other.splice(this.deleteItemIdx, 1);
                }
            }
        },
        reload: function() {
            var self = this;
            // run reinit_actions after reload finish
            return this._super.apply(this, arguments).done(function() {
                 self.reinit_actions();
            });
        },
        do_show: function() {
            var self = this;
            // run reinit_actions after do_show finish
            return this._super.apply(this, arguments).done(function() {
                 self.reinit_actions();
            });
        }
    });

    var FitSaltEdgeSynchroniseStart = Widget.extend({
        className: 'fit_saltedge_synchronise_start',
        start: function() {
            var self = this;
            var model = new Model("fit.saltedge.synchronise");
            var synchronise_item_id;
            model.call("create", [{context: new data.CompoundContext()}])
                .then(function (result) {
                    synchronise_item_id = result;
                    console.log('Created new synchronization item: '+synchronise_item_id);
                    self.do_action({
                        type: 'ir.actions.act_window',
                        auto_search: true,
                        view_type: 'form',
                        view_mode: 'form',
                        res_model: 'fit.saltedge.synchronise',
                        res_id: synchronise_item_id,
                        views: [[false, 'form']],
                        target: 'inline',
                    });
                });
        }
    });
    core.action_registry.add('fit.saltedge.synchronise.start', FitSaltEdgeSynchroniseStart );

    var FitSaltEdgeLoginWizardStart = Widget.extend({
        className: 'fit_saltedge_login_wizard_start',
        start: function() {
            var self = this;
            var model = new Model("fit.saltedge.login.wizard");
            var imbus = new Model("bus.bus");
            var login_wizard_id;
            model.call("create", [{context: new data.CompoundContext()}])
                .then(function (result) {
                    login_wizard_id = result;
                    console.log('Created new login wizard item: '+login_wizard_id);
                    self.do_action({
                        type: 'ir.actions.act_window',
                        confirm: 'blablabla',
                        auto_search: true,
                        view_type: 'form',
                        view_mode: 'form',
                        res_model: 'fit.saltedge.login.wizard',
                        res_id: login_wizard_id,
                        views: [[false, 'form']],
                        target: 'inline',
                        context: {},
//                        flags: {form: {action_buttons: False}}
                    });
                });
        }
    });
    core.action_registry.add('fit.saltedge.bank.registration.start', FitSaltEdgeLoginWizardStart );

});