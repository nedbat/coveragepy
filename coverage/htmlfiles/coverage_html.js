// Coverage.py HTML report browser code.
/*jslint browser:true, indent: 4 */
/*global coverage:true, document window $ */

coverage = {};

// Find all the elements with shortkey_* class, and use them to assign a shotrtcut key.
coverage.assign_shortkeys = function () {
    $("*[class*='shortkey_']").each(function (i, e) {
        $.each($(e).attr("class").split(" "), function (i, c) {
            if (/^shortkey_/.test(c)) {
                $(document).bind('keydown', c.substr(9), function () {
                    $(e).click();
                });
            }
        });
    });
};

// Loaded on index.html
coverage.index_ready = function ($) {
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
        format: function (table) {
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
    $(window).unload(function () {
        document.cookie = cookie_name + "=" + sort_list.toString() + "; path=/";
    });
};

// -- pyfile stuff --

coverage.pyfile_ready = function ($) {
    // If we're directed to a particular line number, highlight the line.
    var frag = location.hash;
    if (frag.length > 2 && frag[1] === 'n') {
        $(frag).addClass('highlight');
        coverage.set_sel(parseInt(frag.substr(2), 10));
    }
    else {
        coverage.set_sel(0);
    }

    $(document)
        .bind('keydown', 'j', coverage.to_next_chunk)
        .bind('keydown', 'k', coverage.to_prev_chunk)
        .bind('keydown', '0', coverage.to_top)
        .bind('keydown', '1', coverage.to_first_chunk)
        ;

    coverage.assign_shortkeys();
};

coverage.toggle_lines = function (btn, cls) {
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

// Return the nth line.
coverage.line_elt = function (n) {
    return $("#t" + n);
};

// Return the nth line number.
coverage.num_elt = function (n) {
    return $("#n" + n);
};

// Return the container of all the code.
coverage.code_container = function (n) {
    return $(".linenos");
};

coverage.set_sel = function (b, e) {
    // The first line selected.
    coverage.sel_begin = b;
    // The next line not selected.
    coverage.sel_end = (e === undefined) ? b+1 : e;
};

coverage.to_top = function () {
    coverage.set_sel(0, 1);
    $("html").animate({scrollTop: 0}, 200);
};

coverage.to_first_chunk = function () {
    coverage.set_sel(0, 1);
    coverage.to_next_chunk();
};

coverage.to_next_chunk = function () {
    var c = coverage;

    // Find the start of the next colored chunk.
    var probe = c.sel_end;
    while (true) {
        var probe_line = c.line_elt(probe);
        if (probe_line.length === 0) {
            return;
        }
        var color = probe_line.css("background-color");
        if (color !== "transparent") {
            break;
        }
        probe++;
    }

    // There's a next chunk, `probe` points to it.
    var begin = probe;

    // Find the end of this chunk.
    var next_color = color;
    while (next_color === color) {
        probe++;
        probe_line = c.line_elt(probe);
        next_color = probe_line.css("background-color");
    }
    c.set_sel(begin, probe);
    c.show_selection();
};

coverage.to_prev_chunk = function () {
    var c = coverage;

    // Find the end of the prev colored chunk.
    var probe = c.sel_begin-1;
    var probe_line = c.line_elt(probe);
    if (probe_line.length === 0) {
        return;
    }
    var color = probe_line.css("background-color");
    while (probe > 0 && color === "transparent") {
        probe--;
        probe_line = c.line_elt(probe);
        if (probe_line.length === 0) {
            return;
        }
        color = probe_line.css("background-color");
    }

    // There's a prev chunk, `probe` points to its last line.
    var end = probe+1;

    // Find the beginning of this chunk.
    var prev_color = color;
    while (prev_color === color) {
        probe--;
        probe_line = c.line_elt(probe);
        prev_color = probe_line.css("background-color");
    }
    c.set_sel(probe+1, end);
    c.show_selection();
};

coverage.show_selection = function () {
    var c = coverage;

    // Highlight the lines in the chunk
    c.code_container().find(".highlight").removeClass("highlight");
    for (var probe = c.sel_begin; probe > 0 && probe < c.sel_end; probe++) {
        c.num_elt(probe).addClass("highlight");
    }

    c.scroll_to_selection();
};

coverage.scroll_to_selection = function () {
    // Scroll the page if the chunk isn't fully visible.
    var top = coverage.line_elt(coverage.sel_begin);
    var next = coverage.line_elt(coverage.sel_end);

    if (!top.isOnScreen() || !next.isOnScreen()) {
        // Need to move the page.
        var top_pos = parseInt(top.offset().top, 10);
        $("html").animate({scrollTop: top_pos-30}, 300);
    }
};
