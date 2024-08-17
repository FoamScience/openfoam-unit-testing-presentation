from manim import *
from manim_slides import Slide
from manim.utils import color
from manim.utils.color import interpolate_color
from numpy.random import RandomState
import numpy as np
import pandas as pd

rng = RandomState(0)
MAIN_COLOR = color.TEAL_A
BACKGROUND_COLOR = color.GRAY_E
TEXT_COLOR = color.WHITE
GRAPH_COLOR = color.BLUE_B
WARN_COLOR= color.YELLOW_C
DOT_COLOR = color.RED_C
ITEM_ICON = "•"
BOX_BUFF = 0.3
very_small_size = 12.0
small_size = 16
mid_size = 20
big_size = 25
N = 6
Text.set_default(font="Comic Code Ligatures", color=TEXT_COLOR, font_size=small_size)
Code.set_default(font="Comic Code Ligatures", font_size=small_size, style="manni", background="window", tab_width=4, line_spacing=0.65)
Tex.set_default(color=TEXT_COLOR, font_size=small_size)
Dot.set_default(radius=0.07, color=DOT_COLOR)


testable_code = """class MyClass {
protected:
    /// Member reference to the mesh
    const fvMesh& mesh_;

    /// A copy of the dictionary
    dictionary dict_;
public:

    /// Construct
    MyClass(const fvMesh&, const dictionary&);
};

// DB part of the mesh interface is interesting
mesh_.lookupObject<volVectorField>("U") ....
"""

self_configured = """// Build the dictionary content
IStringStream is("parameter "+Foam::name(parameterVal)+';');
IOdictionary annoyingDict
(
    IOobject
    (
        "annoyingDict", runTime.constant(), runTime,
        IOobject::NO_READ, IOobject::NO_WRITE, false
    ),
    is
);
// Write it to disk just before constructing the object
annoyingDict.regIOobject::write();
// Now test construction of the not-so-configurable class
annoyingClass obj(...); // ctor will read annoyingDict
"""

test_case = """TEST_CASE
(
    "Check time index",
    "[cavity][serial][parallel]"
) {
    // Access the global time object
    Time& runTime = *timePtr;

    // Gather important test info
    CAPTURE(runTime.timeIndex());

    // Actual test expression
    REQUIRE(runTime.timeIndex() == 0);
}
"""

test_case_log = """myClassTests.C:13: FAILED:
    REQUIRE( runTime.timeIndex() == 0 )
with expansion:
    1 == 0
with message:
    runTime.timeIndex() := 1
===================================
test cases: 2 | 1 passed | 1 failed
assertions: 3 | 2 passed | 1 failed
"""

orig_code = """#include "baseModel.H"
   
TEST_CASE
(
    "baseModel tests",
    "[cavity][serial][parallel]"
) {
	dictionary config;
    config.set("baseModelType", "concrete1");
	auto skel = generateSchema<baseModel>(config);
	// expensive to construct, has heavy dependencies...
	autoPtr<baseModel> bm = baseModel::New(skel, mesh);
    // test check
    REQUIRE(bm->isEverythingOK());
}"""

handson1 = """class myClass
{
    const fvMesh& mesh_;
    const dictionary& dict_;
    bool velocityIsFound_;
    label setting_;
    bool velocityIsFound() const {return velocityIsFound_;}
public:
    myClass(const fvMesh& mesh, const dictionary& dict)
    : mesh_(mesh), dict_(dict),
        velocityIsFound_(mesh_.foundObject<volVectorField>("U")),
        setting_(readLabel(dict_.lookup("setting")))
    {}
    virtual ~myClass(){}
    label setting() const {return setting_;}
};
"""

handson2 = """/// Solver or production-lib code
IOdictionary dict
(
    IOobject
    (
        "myClassDict",
        runTime.constant(),
        mesh,
        IOobject::MUST_READ,
        IOobject::NO_WRITE
    )
);
/// but trades-off triviality of
/// runtime-modifiability!
myClass myObj(mesh, dict);
"""

handson3 = """/// Test code
dictionary dict;
dict.set("setting", 4);
/// Explicitely documents
/// required keywords
myClass myObj(mesh, dict);
"""

handson4 = """// Catch2 is the unit-testing backend !! Pseudo-code !!
// There is also Signature-parametrised tests
TEMPLATE_TEST_CASE
(
    "Matrix classes work for supported types",
    "[cavity][serial]", scalar, vector, tensor
) {
    // Value-parametrised tests
    auto n = GENERATE(10, 200, 500); auto src = Randomize(n);
    SECTION("source stores the currect entries") {
        Matrix<TestType> matrix(TestType::zero, src);
        REQUIRE_THAT(matrix.source(), Matchers::Approx(src));
    }
    SECTION("LDU Addressing gets constructed correctly") {
        // Similar testing...
        // Checkout Catch2 docs!
    }
}
"""

espionage = """/// Private methods/data ???
using MethodType = bool(myClass::*)(); //< fnc ptr type to method
/// Macros from FoamScience/OpenFOAM-Unit-testing: https://t.ly/birh0
SPECIALIZE_MEMBER_METHOD_STEALER(velocityIsFound, MethodType, myClass);
TEST_CASE
(
    "myClass can querry the mesh DB",
    "[cavity][serial][parallel]"
) {
    dictionary config;
    config.set("setting", 4);
    myClass obj(mesh, config);
    REQUIRE(
        CALL_MEMBER_METHOD(velocityIsFound, myClass, obj) ()
    );
}
"""

timeouts = """#include <csetjmp>
#include <csignal>
jmp_buf project_env; // POSIX signals
void onSigabrt(int signum) {
  signal (signum, SIG_DFL); longjmp (project_env, 1);
}
void tryAndCatchAbortingCode(std::function<void(void)> func) {
    FatalError.dontThrowExceptions(); //< hard fails
    if (setjmp (amr_env) == 0) {
        signal(SIGTERM, &onSigabrt);
        func(); signal(SIGTERM, SIG_DFL);
    } else { REQUIRE(false); }//< Fail the test case 
}
"""

def replace_nth_line(string, n, repl):
    lines = string.splitlines()
    if 0 <= n-1 < len(lines):
        lines[n-1] = repl
    return "\n".join(lines)

def keep_only_objects(slide, grp):
    slide.clear()
    for _ in grp:
        slide.add(_)

class UnitTesting(Slide):

    def itemize(self, items, anchor, distance, stepwise, **kwargs):
        anims = []
        mobjs = []
        for i in range(len(items)):
            mobjs.append(Text(f"{i+1}{ITEM_ICON} {items[i]}", font_size=small_size, **kwargs))
            if i == 0:
                mobjs[i].next_to(anchor, DOWN*distance).align_to(anchor, LEFT)
            else:
                mobjs[i].next_to(mobjs[i-1], DOWN).align_to(mobjs[i-1], LEFT)
        anims = [FadeIn(mobjs[i]) for i in range(len(items))]
        if stepwise:
            for a in anims:
                self.play(a)
        else:
            self.play(AnimationGroup(*anims))
        return mobjs[-1]

    def hi_yaml(self, items, indents, anchor, distance):
        anims = []
        mobjs = []
        for i in range(len(items)):
            mobjs.append(Text(f"{items[i][0]}: {items[i][1]}", font_size=small_size,
                 t2w={f"{items[i][0]}:": BOLD}, t2c={f"{items[i][0]}:": GREEN}))
            if i == 0:
                mobjs[i].next_to(anchor, DOWN*distance).align_to(anchor, LEFT).shift(indents[i]*RIGHT)
            else:
                mobjs[i].next_to(mobjs[i-1], DOWN).align_to(mobjs[i-1], LEFT).shift((indents[i]-indents[i-1])*RIGHT)
        anims = [Create(mobjs[i]) for i in range(len(items))]
        self.play(AnimationGroup(*anims))
        return mobjs[-1]

    def construct(self):
        self.camera.background_color = BACKGROUND_COLOR
        # Title page
        layout = Group()
        title = Text(f"Unit testing OpenFOAM code with foamUT", font_size=big_size)#.to_edge(UP+LEFT)
        footer = Text("NHR4CES", t2w={"NHR4CES": BOLD}, font_size=very_small_size).to_edge(DOWN+RIGHT)
        author = Text("Mohammed Elwardi Fadeli, Sept. 2024", font_size=very_small_size).to_edge(DOWN+LEFT)
        logo = ImageMobject("./images/nhr-tu-logo.png").next_to(title, UP).scale(0.6)#.to_edge(UP+RIGHT)
        layout.add(title, footer, author, logo)
        self.play(FadeIn(layout))
        self.next_slide()

        c1 = Text(f"Plan Features")
        b1 = SurroundingRectangle(c1, color=MAIN_COLOR, buff=BOX_BUFF)
        bg1 = BackgroundRectangle(c1, color=MAIN_COLOR, fill_opacity=0.3, buff=BOX_BUFF)
        vg1 = VGroup(c1, b1, bg1).to_edge(UP).shift(2*(LEFT+DOWN))
        anims =[
            Transform(title, vg1),
            Transform(logo, logo.copy().scale(0.5).to_edge(UP+RIGHT)),
        ]
        self.play(AnimationGroup(*anims))
        self.next_slide()

        c2 = Text(f"Code")
        b2 = SurroundingRectangle(c2, color=MAIN_COLOR, buff=BOX_BUFF)
        bg2 = BackgroundRectangle(c2, color=MAIN_COLOR, fill_opacity=0.3, buff=BOX_BUFF)
        vg2 = VGroup(c2, b2, bg2).next_to(vg1, 1.5*(LEFT+DOWN))
        anims =[
            Create(CurvedArrow(vg1.get_left(), vg2.get_top(), color=MAIN_COLOR)),
            FadeIn(vg2)
        ]
        self.play(AnimationGroup(*anims))
        self.next_slide()

        c3 = Text(f"Build")
        b3 = SurroundingRectangle(c3, color=MAIN_COLOR, buff=BOX_BUFF)
        bg3 = BackgroundRectangle(c3, color=MAIN_COLOR, fill_opacity=0.3, buff=BOX_BUFF)
        vg3 = VGroup(c3, b3, bg3).next_to(vg1, 1.5*4*DOWN)
        anims =[
            Create(CurvedArrow(vg2.get_bottom(), vg3.get_left(), color=MAIN_COLOR)),
            FadeIn(vg3)
        ]
        self.play(AnimationGroup(*anims))
        self.next_slide()

        c4 = Text(f"Testing")
        b4 = SurroundingRectangle(c4, color=MAIN_COLOR, buff=BOX_BUFF)
        bg4 = BackgroundRectangle(c4, color=MAIN_COLOR, fill_opacity=0.3, buff=BOX_BUFF)
        vg4 = VGroup(c4, b4, bg4).next_to(vg1, 1.5*(RIGHT+DOWN))
        anims =[
            Create(CurvedArrow(vg3.get_right(), vg4.get_bottom(), color=MAIN_COLOR)),
            FadeIn(vg4)
        ]
        self.play(AnimationGroup(*anims))
        self.next_slide()

        c5 = Text(f"Release")
        b5 = SurroundingRectangle(c5, color=DOT_COLOR, buff=BOX_BUFF)
        bg5 = BackgroundRectangle(c5, color=DOT_COLOR, fill_opacity=0.3, buff=BOX_BUFF)
        vg5 = VGroup(c5, b5, bg5).next_to(vg4, 1.5*3*DOWN)
        anims =[
            Create(Arrow(b4.get_bottom()+0.5*RIGHT, b5.get_top()+0.5*RIGHT, color=DOT_COLOR, buff=0.1)),
            FadeIn(vg5)
        ]
        self.play(AnimationGroup(*anims))
        self.next_slide()

        c6 = Text(f"Deploy")
        b6 = SurroundingRectangle(c6, color=DOT_COLOR, buff=BOX_BUFF)
        bg6 = BackgroundRectangle(c6, color=DOT_COLOR, fill_opacity=0.3, buff=BOX_BUFF)
        vg6 = VGroup(c6, b6, bg6).next_to(vg4, 1.5*(DOWN+RIGHT))
        anims =[
            Create(CurvedArrow(vg5.get_bottom(), vg6.get_bottom(), color=DOT_COLOR)),
            FadeIn(vg6)
        ]
        self.play(AnimationGroup(*anims))
        self.next_slide()

        self.play(
            Create(CurvedArrow(vg6.get_top(), vg4.get_right(), color=DOT_COLOR)),
        )
        self.next_slide()
        self.play(
            Create(CurvedArrow(vg4.get_top(), vg1.get_right(), color=DOT_COLOR)),
        )
        self.next_slide()

        layout.remove(title)
        title = Text(f"0.0 Why unit-test OpenFOAM code?", t2w={"0.": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        layout.add(title)
        diagram = VGroup(vg1, vg2, vg3, vg4, vg5, vg6)
        keep_only_objects(self, Group(layout, diagram))
        self.play(Transform(diagram, title))
        self.next_slide()

        objs = Text("- Enforcing Intention-Code 'strong coupling':", font_size=mid_size).next_to(title, DOWN*2).align_to(title, LEFT)
        self.play(Create(objs))
        items = [
            "New functionality works as intended.",
            "Backward-compatibility, and catching (unintended) breaking changes.",
            "Example-based documentation of intended usage.",
            "Continuous performance improvement monitoring."
        ]
        last = self.itemize(items, objs, 1.5, False,
            t2w={f"1{ITEM_ICON}": BOLD, f"2{ITEM_ICON}": BOLD, f"3{ITEM_ICON}": BOLD, f"4{ITEM_ICON}": BOLD},
            t2c={f"1{ITEM_ICON}": MAIN_COLOR, f"2{ITEM_ICON}": MAIN_COLOR, f"3{ITEM_ICON}": MAIN_COLOR, f"4{ITEM_ICON}": MAIN_COLOR})
        self.next_slide()

        objs = Text("- Automated tests?", font_size=mid_size).next_to(title, DOWN*14).align_to(title, LEFT)
        self.play(Create(objs))
        items = [
            "Usually unexpensive, testing small code entities.",
            "Automated => discourage frequent API changes.",
            "Easy to run in CI workflows.",
            "Special case: Porting/Refactoring code made safer with unit tests."
        ]
        last = self.itemize(items, objs, 1.5, False,
            t2w={f"1{ITEM_ICON}": BOLD, f"2{ITEM_ICON}": BOLD, f"3{ITEM_ICON}": BOLD, f"4{ITEM_ICON}": BOLD},
            t2c={f"1{ITEM_ICON}": MAIN_COLOR, f"2{ITEM_ICON}": MAIN_COLOR, f"3{ITEM_ICON}": MAIN_COLOR, f"4{ITEM_ICON}": MAIN_COLOR})
        self.next_slide()

        t2 = Text(f"1.1 What OpenFOAM code to test?", t2w={"1.1": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        keep_only_objects(self, Group(layout))
        self.play(Transform(title, t2))
        self.next_slide()

        objs = Text("- Effective unit-testing takes:", font_size=mid_size).next_to(title, DOWN*2).align_to(title, LEFT)
        self.play(Create(objs))
        items = [
            "Writing test-friendly code in the first place.",
            "Prioritizing testing of Public Intefaces.",
            "Guarding against breaking changes in crucial external dependencies.",
        ]
        last = self.itemize(items, objs, 1.5, False,
            t2w={f"1{ITEM_ICON}": BOLD, f"2{ITEM_ICON}": BOLD, f"3{ITEM_ICON}": BOLD, f"4{ITEM_ICON}": BOLD},
            t2c={f"1{ITEM_ICON}": MAIN_COLOR, f"2{ITEM_ICON}": MAIN_COLOR, f"3{ITEM_ICON}": MAIN_COLOR, f"4{ITEM_ICON}": MAIN_COLOR})
        self.next_slide()

        objs = Text("- Test-friendly code?", font_size=mid_size).next_to(title, DOWN*12).align_to(title, LEFT)
        self.play(Create(objs))
        items = [
            "Minimal interfacing with Disk IO, databases, external protocols ... etc.",
            "Private members should not be candidates for testing.",
            "Stable-enough APIs...",
            "Classes can be configured from outside code (code external to them)."
        ]
        last = self.itemize(items, objs, 1.5, False,
            t2w={f"1{ITEM_ICON}": BOLD, f"2{ITEM_ICON}": BOLD, f"3{ITEM_ICON}": BOLD, f"4{ITEM_ICON}": BOLD},
            t2c={f"1{ITEM_ICON}": MAIN_COLOR, f"2{ITEM_ICON}": MAIN_COLOR, f"3{ITEM_ICON}": MAIN_COLOR, f"4{ITEM_ICON}": MAIN_COLOR})
        self.next_slide()

        t3 = Text(f"1.2 How to perform OpenFOAM code tests?", t2w={"1.2": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        keep_only_objects(self, Group(layout))
        self.play(Transform(title, t3))
        self.next_slide()

        objs = Text("- Isolation:", font_size=mid_size).next_to(title, DOWN*2).align_to(title, LEFT)
        self.play(Create(objs))
        items = [
            "Each class is tested in its default state (configuration).",
            "Dependencies for construction should be generated on-the-fly.",
            "Unit tests should not write to peripherals (disks, databases ... etc).",
            "Unit tests should throw exceptions..."
        ]
        last = self.itemize(items, objs, 1.5, False,
            t2w={f"1{ITEM_ICON}": BOLD, f"2{ITEM_ICON}": BOLD, f"3{ITEM_ICON}": BOLD, f"4{ITEM_ICON}": BOLD},
            t2c={f"1{ITEM_ICON}": MAIN_COLOR, f"2{ITEM_ICON}": MAIN_COLOR, f"3{ITEM_ICON}": MAIN_COLOR, f"4{ITEM_ICON}": MAIN_COLOR})
        self.next_slide()

        objs = Text("- Production parity:", font_size=mid_size).next_to(title, DOWN*13).align_to(title, LEFT)
        self.play(Create(objs))
        items = [
            "Stay as close as possible to 'standard usage' of classes.",
            "Including the way their dependencies are built.",
            "And even compiler and linker settings.",
            "Eg. expect to dynamically load stuff? that's how you test them."
        ]
        last = self.itemize(items, objs, 1.5, False,
            t2w={f"1{ITEM_ICON}": BOLD, f"2{ITEM_ICON}": BOLD, f"3{ITEM_ICON}": BOLD, f"4{ITEM_ICON}": BOLD},
            t2c={f"1{ITEM_ICON}": MAIN_COLOR, f"2{ITEM_ICON}": MAIN_COLOR, f"3{ITEM_ICON}": MAIN_COLOR, f"4{ITEM_ICON}": MAIN_COLOR})
        self.next_slide()

        t4 = Text(f"2.1 Write testable code - Basics", t2w={"2.1": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        keep_only_objects(self, Group(layout))
        self.play(Transform(title, t4))
        self.next_slide()

        code_t = testable_code
        for i in [3,4,6,7,14,15]:
            code_t = replace_nth_line(code_t, i, " "*len(testable_code.splitlines()[i-1]))
        code_t = replace_nth_line(code_t, 11, "    MyClass();")
        code = Code(code=code_t, language="cpp").to_edge(RIGHT)
        self.play(Create(code))
        self.next_slide()

        code_t = testable_code
        for i in [6,7]:
            code_t = replace_nth_line(code_t, i, " "*len(testable_code.splitlines()[i-1]))
        code_t = replace_nth_line(code_t, 11, "    MyClass(const fvMesh&);")
        code1 = Code(code=code_t, language="cpp").to_edge(RIGHT)
        self.play(Transform(code, code1))
        self.next_slide()

        ev1 = Text(r"Access to important objects", line_spacing=0.4, font_size=small_size)
        ev1.next_to(code1, LEFT).shift(0.5*DOWN)
        ev2 = Text(r"with little API dependency", line_spacing=0.4, font_size=small_size).next_to(ev1, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        ev1 = Text(r"Having a reference can", line_spacing=0.4, font_size=small_size, color=DOT_COLOR)
        ev1.next_to(code1, LEFT).shift(UP)
        ev2 = Text(r"complicate MPI comms", line_spacing=0.4, font_size=small_size, color=DOT_COLOR).next_to(ev1, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        keep_only_objects(self, Group(layout, code1))
        code2 = Code(code=testable_code, language="cpp").to_edge(RIGHT)
        self.play(Transform(code1, code2))
        self.next_slide()

        ev1 = Text(r"Caller is responsible", line_spacing=0.4, font_size=small_size)
        ev1.next_to(code1, LEFT).shift(0.2*UP)
        ev2 = Text(r"for configuration", line_spacing=0.4, font_size=small_size).next_to(ev1, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        ev1 = Text(r"Required entries in dict_", line_spacing=0.4, font_size=small_size, color=GREEN)
        ev1.next_to(code1, LEFT).shift(1.5*UP)
        ev2 = Text(r"are explicitly documented", line_spacing=0.4, font_size=small_size, color=GREEN).next_to(ev1, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        t5 = Text(f"2.2 Not so-test-friendly classes!", t2w={"2.2": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        keep_only_objects(self, Group(layout))
        self.play(Transform(title, t5))
        self.next_slide()

        code = Code(code=self_configured, language="cpp")
        self.play(Create(code))
        self.next_slide()

        t6 = Text(f"2.3 foamUT: Effective OpenFOAM unit-testing", t2w={"2.3": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        keep_only_objects(self, Group(layout))
        self.play(Transform(title, t6))
        self.next_slide()

        im = ImageMobject("./images/foamUT-qr.png").scale(0.3).to_corner(RIGHT+DOWN).shift(UP)

        c1 = Text(f"myClassTests.C")
        b1 = SurroundingRectangle(c1, color=MAIN_COLOR, buff=BOX_BUFF)
        bg1 = BackgroundRectangle(c1, color=MAIN_COLOR, fill_opacity=0.3, buff=BOX_BUFF)
        vg1 = VGroup(c1, b1, bg1).shift(0.5*DOWN)
        c1s = Text(f"serial").next_to(c1, RIGHT+UP, BOX_BUFF, LEFT).shift(0.1*UP)
        c1p = Text(f"parallel").next_to(c1, RIGHT+DOWN, BOX_BUFF, LEFT).shift(0.1*DOWN)

        c2 = Text(f"Make")
        b2 = SurroundingRectangle(c2, color=MAIN_COLOR, buff=BOX_BUFF)
        bg2 = BackgroundRectangle(c2, color=MAIN_COLOR, fill_opacity=0.3, buff=BOX_BUFF)
        vg2 = VGroup(c2, b2, bg2).next_to(vg1, 3*LEFT)
        bb = SurroundingRectangle(Group(vg1, vg2, c1s, c1p), color=MAIN_COLOR, buff=BOX_BUFF)
        c1t = Text(f"tests", color=MAIN_COLOR).next_to(bb, DOWN, BOX_BUFF)
        self.play(FadeIn(vg1, vg2, c1s, c1p, bb, c1t, im))
        self.next_slide()

        c3 = Text(f"src/libs")
        b3 = SurroundingRectangle(c3, color=DOT_COLOR, buff=BOX_BUFF)
        bg3 = BackgroundRectangle(c3, color=DOT_COLOR, fill_opacity=0.3, buff=BOX_BUFF)
        vg3 = VGroup(c3, b3, bg3).next_to(bb, 3*(LEFT+UP))
        self.play(
            FadeIn(vg3),
            Create(CurvedArrow(vg3.get_bottom(), bb.get_left() , color=DOT_COLOR)),
        )
        self.next_slide()

        cbb = VGroup(bb, c1t)
        n1 = cbb.get_corner(UP+RIGHT)+ 0.5*(UP+RIGHT)
        n2 = vg3.get_corner(UP+RIGHT)+ 0.5*(UP+RIGHT)
        n12 = n1*UP + n2*RIGHT
        n3 = vg3.get_corner(UP+LEFT)+ 0.5*(UP+LEFT)
        n4 = cbb.get_corner(DOWN+RIGHT)+ 0.5*(DOWN+RIGHT)
        n34 = n3*RIGHT + n4*UP
        kbb = Polygon(n1,n12,n2,n3,n34,n4, color=YELLOW, fill_opacity=0.1, fill_color=YELLOW)
        kbbt = Text("your repository", color=YELLOW).next_to(n34, UP+RIGHT)
        self.play(FadeIn(kbb, kbbt))

        c4 = Text(f"Test driver")
        b4 = SurroundingRectangle(c4, color=YELLOW, buff=BOX_BUFF)
        vg4 = VGroup(c4, b4).next_to(bb, 4.5*UP)
        self.play(
            FadeIn(vg4),
            Create(Arrow(bb.get_top(), vg4.get_bottom(), color=YELLOW, buff=0.1)),
        )
        self.next_slide()

        c5 = Text(f"OpenFOAM cases")
        b5 = SurroundingRectangle(c5, color=DOT_COLOR, buff=BOX_BUFF)
        bg5 = BackgroundRectangle(c5, color=DOT_COLOR, fill_opacity=0.3, buff=BOX_BUFF)
        vg5 = VGroup(c5, b5, bg5).next_to(bb, 4.5*(UP+RIGHT))
        self.play(
            FadeIn(vg5),
            Create(Arrow(vg4.get_right(), vg5.get_left(), color=YELLOW, buff=0.1)),
        )
        self.next_slide()

        self.play(vg1.animate.scale(1.5))
        keep_only_objects(self, Group(layout, vg1))
        self.play(Transform(vg1, Code(code=test_case, language="cpp").to_edge(RIGHT)))
        self.next_slide()

        ev1 = Text(r"Test case tagging with", line_spacing=0.4, font_size=small_size)
        ev1.next_to(vg1, LEFT).shift(1.5*UP)
        ev2 = Text(r"OF case name, and", line_spacing=0.4, font_size=small_size).next_to(ev1, 0.5*DOWN)
        ev3 = Text(r"run mode", line_spacing=0.4, font_size=small_size).next_to(ev2, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2, ev3)))
        self.next_slide()

        ev1 = Text(r"foamUT provides a time obj", line_spacing=0.4, font_size=small_size, color=GREEN)
        ev1.next_to(vg1, LEFT)
        self.play(FadeIn(ev1))
        self.next_slide()

        ev1 = Text(r"Reporting is 1st-class citizen", line_spacing=0.4, font_size=small_size, color=MAIN_COLOR)
        ev1.next_to(vg1, LEFT).shift(0.75*DOWN)
        self.play(FadeIn(ev1))
        self.next_slide()

        ev1 = Text(r"Catch2 expressions evaluation", line_spacing=0.4, font_size=small_size, color=MAIN_COLOR)
        ev1.next_to(vg1, LEFT).shift(1.5*DOWN)
        self.play(FadeIn(ev1))
        self.next_slide()

        keep_only_objects(self, Group(layout, vg1))
        self.play(Transform(vg1, Code(
            code=test_case_log,
            language="Makefile",
        )))
        self.next_slide()

        keep_only_objects(self, Group(layout))
        t7 = Text(f"2.4 Basic foamUT usage - Hands-on", t2w={"2.4": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        self.play(Transform(title, t7))
        self.next_slide()

        code = Code(code=handson1, language="cpp")
        self.play(Create(code))
        self.next_slide()

        code_t = VGroup(
            Code(code=handson2, language="cpp").to_edge(RIGHT),
            Code(code=handson3, language="cpp").to_edge(LEFT),
        )
        self.play(Transform(code, code_t))
        self.next_slide()

        keep_only_objects(self, Group(layout))
        t8 = Text(f"2.5 Advanced foamUT usage - Hands-on", t2w={"2.5": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        self.play(Transform(title, t8))
        self.next_slide()

        code = Code(code=handson4, language="cpp")
        self.play(Create(code))
        self.next_slide()

        keep_only_objects(self, layout)
        t9 = Text(f"2.6 Advanced foamUT usage - Espionage Mode", t2w={"2.6": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        self.play(Transform(title, t9))
        self.next_slide()

        code = Code(code=espionage, language="cpp")
        self.play(Create(code))
        self.next_slide()
        
        tx = Text(f"PLEASE don't do this for YOUR classes though!", t2w={"PLEASE": BOLD, "YOUR": BOLD}, color=DOT_COLOR).next_to(code,DOWN)
        self.play(FadeIn(tx, Line(code.get_corner(UP+RIGHT), code.get_corner(LEFT+DOWN), color=DOT_COLOR, stroke_width=3)))
        self.next_slide()

        keep_only_objects(self, layout)
        t10 = Text(f"2.7 Advanced foamUT usage - CI setup", t2w={"2.7": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        code = Code(code=timeouts, language="cpp")
        self.play(Transform(title, t10), Create(code))
        self.next_slide()
        
        tx = Text(f"POSIX signaling works for serial tests", color=GRAPH_COLOR).next_to(code,DOWN)
        ty = Text(f"What about MPI race conditions??? -> no graceful recovery guarantees!", color=DOT_COLOR).next_to(tx,0.7*DOWN)
        self.play(FadeIn(tx, ty))
        self.next_slide()

        keep_only_objects(self, layout)
        t11 = Text(f"3.1 Testing RTS Classes in a perfect world", t2w={"3.1": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        self.play(Transform(title, t11))
        self.next_slide()

        code_t = orig_code
        for i in [8, 9, 10]:
            code_t = replace_nth_line(code_t, i, "   ")
        code_t = replace_nth_line(code_t, 12, "    autoPtr<baseModel> bm = baseModel::New(mesh);")
        code = Code(code=code_t, language="cpp").to_edge(RIGHT)
        self.play(Create(code))
        self.next_slide()

        ev1 = Text(r"Only include the", t2w={"Only": BOLD}, line_spacing=0.4, font_size=small_size)
        ev1.next_to(code, LEFT).shift(UP * 2)
        ev2 = Text(r"RTS base header", line_spacing=0.4, font_size=small_size).next_to(ev1, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        ev1 = Text(r"Create a concrete object", t2w={"concrete": BOLD}, line_spacing=0.4, font_size=small_size)
        ev1.next_to(code, LEFT).shift(1.2*DOWN)
        ev2 = Text(r"and test its interface", line_spacing=0.4, font_size=small_size).next_to(ev1, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        ev1 = Text(r"Painful SetUp???", t2c={"Painful SetUp???": WARN_COLOR}, line_spacing=0.4, font_size=small_size)
        ev1.next_to(code, LEFT).shift(0.2*DOWN)
        self.play(FadeIn(ev1))
        self.next_slide()

        keep_only_objects(self, Group(layout, code))
        code_t = orig_code
        for i in [8, 9]:
            code_t = replace_nth_line(code_t, i, "   ")
        code_t = replace_nth_line(code_t, 10, "    auto skel = generateSchema<baseModel>();")
        code2 = Code(code=code_t, language="cpp").to_edge(RIGHT)

        ev1 = Text(r"Generate a config", t2w={"config": BOLD}, line_spacing=0.4, font_size=small_size)
        ev1.next_to(code2, LEFT).shift(DOWN * 0.1)
        ev2 = Text(r"skeleton first", t2w={"skeleton": BOLD}, line_spacing=0.4, font_size=small_size).next_to(ev1, 0.5*DOWN)
        self.play(FadeTransformPieces(code, code2), FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        ev1 = Text(r"Challenge 1: must match", t2w={"Challenge 1:": BOLD}, t2c={"Challenge 1:": DOT_COLOR}, line_spacing=0.4, font_size=small_size)
        ev1.next_to(code2, LEFT).shift(UP)
        ev2 = Text(r"ctor-defaulted members", t2w={"skeleton": BOLD}, line_spacing=0.4, font_size=small_size).next_to(ev1, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        ev1 = Text(r"Challenge 2: do Chal. 1", t2w={"Challenge 2:": BOLD, "Chal. 1": BOLD}, t2c={"Challenge 2:": DOT_COLOR, "Chal. 1": DOT_COLOR}, line_spacing=0.4, font_size=small_size)
        ev1.next_to(code2, LEFT).shift(UP * 2)
        ev2 = Text(r"mostly at compile-time", t2w={"skeleton": BOLD}, line_spacing=0.4, font_size=small_size).next_to(ev1, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        keep_only_objects(self, Group(layout, code2))
        code3 = Code(code=orig_code, language="cpp").to_edge(RIGHT)

        ev1 = Text(r"Oops, need to create a", t2c={"Oops,": WARN_COLOR}, line_spacing=0.4, font_size=small_size)
        ev1.next_to(code3, LEFT).shift(DOWN)
        ev2 = Text(r"concrete object", t2w={"concrete object": BOLD}, line_spacing=0.4, font_size=small_size).next_to(ev1, 0.5*DOWN)
        self.play(Swap(code2, code3), FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        ev1 = Text(f"{ITEM_ICON} passing config helps", t2c={f"{ITEM_ICON}": WARN_COLOR}, line_spacing=0.4, font_size=small_size)
        ev1.next_to(code3, 2*LEFT)
        ev2 = Text(r"with nested models", line_spacing=0.4, font_size=small_size).next_to(ev1, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        ev1 = Text(f"{ITEM_ICON} can abuse the RTS", t2c={f"{ITEM_ICON}": WARN_COLOR}, line_spacing=0.4, font_size=small_size)
        ev1.next_to(code3, LEFT*2).shift(UP)
        ev2 = Text(r"mechanism", line_spacing=0.4, font_size=small_size).next_to(ev1, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        keep_only_objects(self, Group(layout, code3))

        ev1 = Text(r"Still including only", line_spacing=0.4, font_size=small_size)
        ev1.next_to(code3, LEFT).shift(UP * 2)
        ev2 = Text(r"the base header", line_spacing=0.4, font_size=small_size).next_to(ev1, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2)))
        self.next_slide()

        ev1 = Text(r"Super-convenient SetUp", t2c={"Super-convenient": MAIN_COLOR}, line_spacing=0.4, font_size=small_size)
        ev1.next_to(code3, LEFT).shift(0.2*DOWN)
        self.play(FadeIn(ev1))
        self.next_slide()

        ev1 = Text(r"can remove/add class", line_spacing=0.4, font_size=small_size, color=GRAPH_COLOR)
        ev1.next_to(code3, LEFT).shift(1.2*DOWN)
        ev2 = Text(r"members without the", line_spacing=0.4, font_size=small_size, color=GRAPH_COLOR).next_to(ev1, 0.5*DOWN)
        ev3 = Text(r"need to update test", line_spacing=0.4, font_size=small_size, color=GRAPH_COLOR).next_to(ev2, 0.5*DOWN)
        ev4 = Text(r"code", line_spacing=0.4, font_size=small_size, color=GRAPH_COLOR).next_to(ev3, 0.5*DOWN)
        self.play(FadeIn(VGroup(ev1, ev2, ev3, ev4)))
        self.next_slide()

        keep_only_objects(self, layout)

        objs = Text("- Objectives again?", font_size=mid_size).next_to(title, DOWN*2).align_to(title, LEFT)
        self.play(Create(objs))

        items = [
            "Test in an isolated environment.",
            "but keep it identical to real-world solvers.",
            "The unit tests are (always-up-to-date) documentation.",
            "with minimal burden on the programmer (i.e. Test author)."
        ]
        last = self.itemize(items, objs, 1.5, False,
            t2w={f"1{ITEM_ICON}": BOLD, f"2{ITEM_ICON}": BOLD, f"3{ITEM_ICON}": BOLD, f"4{ITEM_ICON}": BOLD},
            t2c={f"1{ITEM_ICON}": GREEN, f"2{ITEM_ICON}": GREEN, f"3{ITEM_ICON}": GREEN, f"4{ITEM_ICON}": GREEN})
        self.next_slide()

        objs = Text("- How much can we realistically achieve?", font_size=mid_size).next_to(title, DOWN*14).align_to(title, LEFT)
        self.play(Create(objs))

        items = [
            "Isolated environment? not really! eg. dependency on a mesh.",
            "foamUT sets up testing drivers as native solver code.",
            "Reflections go a long way, but sacrifices to be made! eg. API Design constraints."
        ]
        last = self.itemize(items, objs, 1.5, False,
            t2w={f"1{ITEM_ICON}": BOLD, f"2{ITEM_ICON}": BOLD, f"3{ITEM_ICON}": BOLD, f"4{ITEM_ICON}": BOLD},
            t2c={f"1{ITEM_ICON}": GREEN, f"2{ITEM_ICON}": GREEN, f"3{ITEM_ICON}": GREEN, f"4{ITEM_ICON}": GREEN})
        self.next_slide()

        keep_only_objects(self, layout)
        t12 = Text(f"3.2 Reflections for unit-testing", t2w={"3.2": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        self.play(Transform(title, t12))

        objs = Text("- A little bit of setup can get us:", font_size=mid_size).next_to(title, DOWN*2).align_to(title, LEFT)
        self.play(Create(objs))

        items = [
            "Automatically-generated dictionaries of required keywords for a class -> generic.",
            "The skeleton dicts get built (mostly) at compile-time -> generic.",
            "These skeleton dicts can fetch default-values that constuctors will set -> special.",
        ]
        last = self.itemize(items, objs, 1.5, False,
            t2w={f"1{ITEM_ICON}": BOLD, f"2{ITEM_ICON}": BOLD, f"3{ITEM_ICON}": BOLD, f"4{ITEM_ICON}": BOLD},
            t2c={f"1{ITEM_ICON}": GREEN, f"2{ITEM_ICON}": GREEN, f"3{ITEM_ICON}": GREEN, f"4{ITEM_ICON}": GREEN, "-> special": GRAPH_COLOR, "-> generic": GRAPH_COLOR})

        self.next_slide()

        objs = Text("- Fetching default values accurately is important because:", font_size=mid_size).next_to(title, DOWN*13).align_to(title, LEFT)
        self.play(Create(objs))

        items = [
            "No one wants to test non-standard class configurations prematurely",
            "But if you need to, fetch default-values skeleton and mutate it!",
            "Ctor sets default values, skeletons generated at compile-time, how does that work?",
            "Obviously, shouldn't have to construct the object to get its members' defaults!"
        ]
        last = self.itemize(items, objs, 1.5, False,
            t2w={f"1{ITEM_ICON}": BOLD, f"2{ITEM_ICON}": BOLD, f"3{ITEM_ICON}": BOLD, f"4{ITEM_ICON}": BOLD},
            t2c={f"1{ITEM_ICON}": GREEN, f"2{ITEM_ICON}": GREEN, f"3{ITEM_ICON}": GREEN, f"4{ITEM_ICON}": GREEN})
        self.next_slide()

        t13 = Text(f"4.1 Success stories", t2w={"4.1": BOLD}, font_size=big_size).to_edge(UP+LEFT)
        keep_only_objects(self, layout)
        self.play(Transform(title, t13))
        self.next_slide()

        bamr = ImageMobject("./images/bamr.png").shift(3*LEFT).scale(0.3).shift(UP)
        tbamr1 = Text(f"STFS-TUDa/blastAMR", color=GREEN).next_to(bamr, DOWN)
        tbamr2 = Text(f"25% git adds/dels for tests/").next_to(tbamr1, DOWN)
        tbamr3 = Text(f"Includes custom cases, with history").next_to(tbamr2, DOWN)
        self.play(FadeIn(bamr, tbamr1, tbamr2, tbamr3))
        self.next_slide()

        ref = ImageMobject("./images/reflections.png").shift(3*RIGHT).scale(0.3).shift(UP)
        tr1 = Text(f"FoamScience/openfoam-reflections", color=GREEN).next_to(ref, DOWN)
        tr2 = Text(f"Unit tests are most of the docs").next_to(tr1, DOWN)
        tr3 = Text(f"Porting features control!").next_to(tr2, DOWN)
        self.play(FadeIn(ref, tr1, tr2, tr3))
        self.next_slide()

        keep_only_objects(self, layout)
        smartsim = ImageMobject("./images/smartsim.png").shift(3*LEFT).scale(0.3).shift(UP)
        ts1 = Text(f"OFDataCommittee/openfoam-smartsim", color=GREEN).next_to(smartsim, DOWN)
        ts2 = Text(f"0.2% git adds/dels for tests/").next_to(ts1, DOWN)
        ts3 = Text(f"Super-efficient testing").next_to(ts2, DOWN)
        self.play(FadeIn(smartsim, ts1, ts2, ts3))
        self.next_slide()

        def discussion(logo, color, user, msg):
            imlg = SVGMobject(logo, height=1)
            imlg.set_color(color)
            t = Text(user, font_size=mid_size, color=color).next_to(imlg, RIGHT, buff=0.1).shift(0.25*UP)
            txt = Text(msg, font_size=small_size).next_to(t, DOWN, buff=0.2).align_to(t, LEFT)
            return Group(imlg, t, txt)

        l1 = Line(3*UP, 3*DOWN, color=GRAPH_COLOR)
        tp1 = Text(f"OpenFOAM v2406 lands", t2w={'OpenFOAM v2406 lands': BOLD}).next_to(l1, RIGHT).shift(2.5*UP)
        self.play(FadeIn(l1, tp1))
        self.next_slide()

        gr1 = discussion(
            "./images/user-circle.svg",
            GRAPH_COLOR,
            "Dev1 - 5 mins ago",
            "Has anyone tested the FO with v2406?"
        ).next_to(tp1, DOWN).align_to(tp1, LEFT)
        self.play(FadeIn(gr1))
        self.next_slide()

        gr2 = discussion(
            "./images/user-circle.svg",
            GREEN,
            "Dev2 - 5 mins ago",
            "No, CI only handles v2312 and v2012"
        ).next_to(gr1, DOWN).align_to(gr1, LEFT)
        gr3 = discussion(
            "./images/user-circle.svg",
            GREEN,
            "Dev2 - 4 mins ago",
            "1 sec, let me run the unit tests..."
        ).next_to(gr2, DOWN).align_to(gr2, LEFT)
        gr4 = discussion(
            "./images/user-circle.svg",
            GREEN,
            "Dev2 - 1 secs ago",
            "FO is fine; smth wrong in ur env?"
        ).next_to(gr3, DOWN).align_to(gr3, LEFT)
        self.play(FadeIn(gr2, gr3, gr4))


