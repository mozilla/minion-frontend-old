// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

$(document).ready(function() {
    $("#plugin_results_area").hide();
    //toggle the componenet with class msg_body
    $("#overall_plugin_results_expander").click(function()
    {
        $("#plugin_results_area").slideToggle(500);
    });
});
