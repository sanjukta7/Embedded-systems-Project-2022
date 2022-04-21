# Embedded-systems-Project-2022
Deriving Finite state machine (FSM) from Verilog descriptions in generalized manner
Requirements for running the codes : 
Python
Icarus Verilog 
Jinja2 
PLY
Pytest 
Graphviz 
Pygraphviz 

Steps to run: 
Clone the repository 
Install the given requirements 
Use appropriate Bash Terminal commands

Description: 
Section 1, Parser with Lexical and Syntax analyzer 
Ideally, the generation of an abstract syntax tree is one of the fundamental ways to tackle this problem of lexical and syntax analyzer. I have used the output AST in the form of nested python class objects. An example of the same is highlighted in the file named “stopwatch.v” which is a FSM described as a stopwatch function in verilog. To code the parser, I primarily use PLY, which is an implementation of preliminary python parsing tools. ( http://www.dabeaz.com/ply/ )

Section 2, Dataflow Analyzer 
The output from this section is used as an intermediate to obtain the control flow analyzer. It is implemented using a visitor pattern i.e. each visited AST node is called by its class name recursively. 
In the first iteration, the inputs, outputs and parameters from the AST are analyzed. The localparams or constant values are defined in the second iteration. The module hierarchy is also determined during this iteration. The data flow graph is thus generated using the hierarchy. 

Section 3, Control-flow Analyzer 
FSM here is treated as a control flow graph. The conditions of signal values such as ‘state’ are modified and signal values for the next analysis step are determined. We provide the outputs for verilog files in the Detailed Evaluation section.

