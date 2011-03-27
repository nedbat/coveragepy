// Coverage.py HTML report browser code.
/*jslint browser:true, indent: 4 */
/*global coverage:true, document window $ */

coverage = {};

// Find all the elements with shortkey_* class, and use them to assign a shotrtcut key.
coverage.assign_shortkeys = function() {
    $("*[class*='shortkey_']").each(function(i, e) {
        $.each($(e).attr("class").split(" "), function(i, c) {
            if (/^shortkey_/.test(c)) {
                $(document).bind('keydown', c.substr(9), function() {
                    $(e).click();
                });
            }
        });
    });
};

// Loaded on index.html
coverage.index_ready = function($) {
    // Look for a cookie containing previous sort settings:
    var sort_list = [];
    var cookie_name = "COVERAGE_INDEX_SORT";
    var i;

    // This almost makes it worth installing the jQuery cookie plugin:
    if (document.cookie.indexOf(cookie_name) > -1) {
        var cookies = document.cookie.split(";");
        for (i = 0; i < cookies.length; i++) {
            var parts = cookies[i].split("=");

            if ($.trim(parts[0]) === cookie_name && parts[1]) {
                sort_list = eval("[[" + parts[1] + "]]");
                break;
            }
        }
    }

    // Create a new widget which exists only to save and restore
    // the sort order:
    $.tablesorter.addWidget({
        id: "persistentSort",

        // Format is called by the widget before displaying:
        format: function(table) {
            if (table.config.sortList.length === 0 && sort_list.length > 0) {
                // This table hasn't been sorted before - we'll use
                // our stored settings:
                $(table).trigger('sorton', [sort_list]);
            }
            else {
                // This is not the first load - something has
                // already defined sorting so we'll just update
                // our stored value to match:
                sort_list = table.config.sortList;
            }
        }
    });

    // Configure our tablesorter to handle the variable number of
    // columns produced depending on report options:
    var headers = {};
    var col_count = $("table.index > thead > tr > th").length;

    headers[0] = { sorter: 'text' };
    for (i = 1; i < col_count-1; i++) {
        headers[i] = { sorter: 'digit' };
    }
    headers[col_count-1] = { sorter: 'percent' };

    // Enable the table sorter:
    $("table.index").tablesorter({
        widgets: ['persistentSort'],
        headers: headers
    });

    coverage.assign_shortkeys();

    // Watch for page unload events so we can save the final sort settings:
    $(window).unload(function() {
        document.cookie = cookie_name + "=" + sort_list.toString() + "; path=/";
    });
};

// -- pyfile stuff --

coverage.pyfile_ready = function($) {
    // If we're directed to a particular line number, highlight the line.
    var frag = location.hash;
    if (frag.length > 2 && frag[1] === 'n') {
        $(frag).addClass('highlight');
        coverage.sel_begin = parseInt(frag.substr(2));
        coverage.sel_end = coverage.sel_begin + 1;
    }

    $(document).bind('keydown', 'j', coverage.to_next_chunk);
    $(document).bind('keydown', 'k', coverage.to_prev_chunk);
    $(document).bind('keydown', '0', coverage.to_top);
    $(document).bind('keydown', '1', coverage.to_first_chunk);

    coverage.assign_shortkeys();
};

coverage.toggle_lines = function(btn, cls) {
    btn = $(btn);
    var hide = "hide_"+cls;
    if (btn.hasClass(hide)) {
        $("#source ."+cls).removeClass(hide);
        btn.removeClass(hide);
    }
    else {
        $("#source ."+cls).addClass(hide);
        btn.addClass(hide);
    }
};

// The first line selected, and the next line not selected.
coverage.sel_begin = 0;
coverage.sel_end = 1;

coverage.to_top = function() {
    coverage.sel_begin = 0;
    coverage.sel_end = 1;
    $("html").animate({scrollTop: 0}, 200);
}

coverage.to_first_chunk = function() {
    coverage.sel_begin = 0;
    coverage.sel_end = 1;
    coverage.to_next_chunk();
}

coverage.to_next_chunk = function() {
    var c = coverage; 

    // Find the start of the next colored chunk.
    var probe = c.sel_end;
    var color = $("#t" + probe).css("background-color");
    while (color === "transparent") {
        probe += 1;
        var probe_line = $("#t" + probe);
        if (probe_line.length === 0) {
            return;
        }
        color = probe_line.css("background-color");
    }

    // There's a next chunk, `probe` points to it.
    c.sel_begin = probe;

    // Find the end of this chunk.
    var next_color = color;
    while (next_color === color) {
        probe += 1;
        next_color = $("#t" + probe).css("background-color");
    }
    c.sel_end = probe;
    coverage.show_selected_chunk();
};

coverage.to_prev_chunk = function() {
    var c = coverage; 

    // Find the end of the prev colored chunk.
    var probe = c.sel_begin-1;
    var color = $("#t" + probe).css("background-color");
    while (probe > 0 && color === "transparent") {
        probe -= 1;
        var probe_line = $("#t" + probe);
        if (probe_line.length === 0) {
            return;
        }
        color = probe_line.css("background-color");
    }

    // There's a prev chunk, `probe` points to its last line.
    c.sel_end = probe+1;

    // Find the beginning of this chunk.
    var prev_color = color;
    while (prev_color === color) {
        probe -= 1;
        prev_color = $("#t" + probe).css("background-color");
    }
    c.sel_begin = probe+1;
    coverage.show_selected_chunk();
};

coverage.show_selected_chunk = function() {
    var c = coverage;

    // Highlight the lines in the chunk
    $(".linenos p").removeClass("highlight");
    var probe = c.sel_begin;
    while (probe > 0 && probe < c.sel_end) {
        $("#n" + probe).addClass("highlight");
        probe += 1;
    }

    // Scroll the page if the chunk isn't fully visible.
    var top = $("#t" + c.sel_begin);
    var bot = $("#t" + (c.sel_end-1));

    if (!top.isOnScreen() || !bot.isOnScreen()) {
        // Need to move the page.
        var top_pos = parseInt(top.offset().top);
        $("html").animate({scrollTop: top_pos-30}, 300);
    }
};

