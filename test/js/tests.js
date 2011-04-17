// Tests of coverage.py HTML report chunk navigation.

// Test helpers

function selection_is(sel) {
    var beg = sel[0], end = sel[1];
    equals(coverage.sel_begin, beg);
    equals(coverage.sel_end, end);
    equals(coverage.code_container().find(".highlight").length, end-beg);
}

function build_fixture(spec) {
    $("#fixture-template").tmpl().appendTo("#qunit-fixture");
    for (var i = 0; i < spec.length; i++) {
        var data = {number: i+1, klass: spec.substr(i, 1)};
        $("#lineno-template").tmpl(data).appendTo("#qunit-fixture .linenos");
        $("#text-template").tmpl(data).appendTo("#qunit-fixture .text");
    }
}

// Tests

$.each([
    ['rrwwrrrr', [1,3], [5,9]],
    ['rb', [1,2], [2,3]],
    ['wrrwrrrrw', [2,4], [5,9]],
    ['rrrbbb', [1,4], [4,7]]
], function(i, params) {

    // Each of these tests uses a fixture with two highlighted chunks.

    var id = params[0];
    var fixture = "#"+id;
    var c1 = params[1];
    var c2 = params[2];

    function setup() {
        build_fixture(id);
    };

    test("first chunk on line 1: "+id, function() {
        setup();
        coverage.to_first_chunk();
        selection_is(c1);
    });

    test("move to next chunk: "+id, function() {
        setup();
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        selection_is(c2);
    });

    test("move to first chunk: "+id, function() {
        setup();
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        coverage.to_first_chunk();
        selection_is(c1);
    });

    test("move to previous chunk: "+id, function() {
        setup();
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        coverage.to_prev_chunk();
        selection_is(c1);
    });

    test("next doesn't move after last chunk: "+id, function() {
        setup();
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        coverage.to_next_chunk();
        selection_is(c2);
    });

    test("prev doesn't move before first chunk: "+id, function() {
        setup();
        coverage.to_first_chunk();
        coverage.to_next_chunk();
        coverage.to_prev_chunk();
        coverage.to_prev_chunk();
        selection_is(c1);
    });

});

test("jump from a line selected", function() {
    build_fixture("rrwwrr");
    coverage.set_sel(3, 4);
    coverage.to_next_chunk();
    selection_is([5,7]);
});
