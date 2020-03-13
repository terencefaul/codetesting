odoo.define('website_secure_page.website', function (require) {
'use strict';
    var ContentMenu = require('website.contentMenu')
    var weWidgets = require('web_editor.widget');
    var weContext = require('web_editor.context');
    ContentMenu.PagePropertiesDialog.include({
        xmlDependencies: weWidgets.Dialog.prototype.xmlDependencies.concat(
            ['/website/static/src/xml/website.pageProperties.xml',
            '/website_secure_page/static/src/xml/website_page.xml']
        ),
        save: function (data) {
            var self = this;
            var context = weContext.get();
            var url = this.$('#page_url').val();

            var $date_publish = this.$("#date_publish");
            $date_publish.closest(".form-group").removeClass('o_has_error').find('.form-control, .custom-select').removeClass('is-invalid');
            var date_publish = $date_publish.val();
            if (date_publish !== "") {
                date_publish = this._parse_date(date_publish);
                if (!date_publish) {
                    $date_publish.closest(".form-group").addClass('o_has_error').find('.form-control, .custom-select').addClass('is-invalid');
                    return;
                }
            }
            var params = {
                id: this.page.id,
                name: this.$('#page_name').val(),
                // Replace duplicate following '/' by only one '/'
                url: url.replace(/\/{2,}/g, '/'),
                is_menu: this.$('#is_menu').prop('checked'),
                is_homepage: this.$('#is_homepage').prop('checked'),
                website_published: this.$('#is_published').prop('checked'),
                create_redirect: this.$('#create_redirect').prop('checked'),
                redirect_type: this.$('#redirect_type').val(),
                website_indexed: this.$('#is_indexed').prop('checked'),
                secure_page: this.$('#secure_page').prop('checked'),
                date_publish: date_publish,
            };
            this._rpc({
                model: 'website.page',
                method: 'save_page_info',
                args: [[context.website_id], params],
            }).then(function (url) {
                // If from page manager: reload url, if from page itself: go to
                // (possibly) new url
                var mo;
                self.trigger_up('main_object_request', {
                    callback: function (value) {
                        mo = value;
                    },
                });
                if (mo.model === 'website.page') {
                    window.location.href = url.toLowerCase();
                } else {
                    window.location.reload(true);
                }
            });
        },
    });
});