## GUI Logging for Gazebo
***Gazebo Design Document***

### Overview

The purpose of this project is to improve logging performance and create
a graphical tool to control log playback.

### Requirements

**Logging performance improvements**

1. Look into HDF as a file format. Compare this to a custom binary format
that is designed for fast recording, and random access.

1. Old and new log files should be accepted by the `gz log` command line
tool, and the graphical interface.

**The GUI should enable users to**

1. Load a log file from disk.
1. Play, pause, rewind, and step through a log.
1. Move to an arbitrary position in the log file using a timestamp or slider.
1. Loop a section of a log file. 

### Architecture

**Gazebo Logging Changes**

* Implement new file format recording in the `gazebo/util/LogRecord` class.
    * This will also touch the `gazebo/physics/World` class, where SDF state
    is currently generated.
* Implement new file format playback in the `gazebo/util/LogPlay` class.
    * This will also touch the `gazebo/physics/World` class, where SDF state
    is currently updated based on an XML string from the current log file.

**Gazebo GUI Changes**

The graphical interface to log playback is a single widget that will be contained in the `gazebo/gui/LogPlayWidget` class.

**Log play GUI components**

* Timeline 
    * A time line, based on a QT slider will be implemented that supports dragging a slider, positioning control points (for loop playback), zooming, and display of time markers. 
* Play,pause,step,skip to beginning, skip to end
    * A set of button located above the time line will allow users to play, pause, step forward/back, and move to the beginning or end of the log.
    * A time box next to the buttons will display the current time position in the log file.
* Zoom and loop tools 
    * Located below the time line is a tool to control the time line zoom level, and wether playback should loop.
* Main render window
    * The main render window will be outlined in orange when a log file is in playback.

**Client-Server communication**

Log playback information will be published over the `~/log/play/info` topic by the server. Log playback control information will be published over the `~/log/play/control` topic by the client.

### Interfaces

Please see [DataLoggingPlayback.pdf](DataLoggingPlayback.pdf) for the
GUI design of the model editor.

**GUI changes**

* A new  menu option `Load Logfile` will be added to the `File` menu in the
menu bar.
* The log play widget will appear when a log file is loaded.
* The log play widget will disappear when the log play widget is closed. When closed, the current world will revert to the previously loaded world.

**gz log changes**

* The `gz log` command line tool will support both the current file format, and the new file format.
* The available commands will remain the same.

### Performance Considerations

The primary performance impact will involve the new log file format. The
chosen format should both record and playback log files more efficiently. In
this case, efficiency is both file size and CPU usage.

In order to test this, we will generate a set of tests to measure the
current log file efficiency. This will provide a baseline against which we
can compare the new file format.

### Tests
Note: figure out a way to keep track of performance measurements in Jenkins.

1. Performance Test: Log record performance
    1. case: Create a world with 1000 falling cubes. Record a log file for
    30 seconds of simulation time. Measure the size of the log file, and
    real-time required to generate the log file.
    1. case: Create a world with 10 double pendulums. Record a lof file for
    30 seconds of simulation time. Measure the size of the log file, and
    real-time required to generate the log file.
1. Performance Test: Log play performance
    1. case: Load and playback the 1000 falling cubes log file. Measure
    real-time to complete log playback. Check to make sure the correct
    sim-time is reached.
    1. case: Load and playback the double pendulums log file. Measure
    real-time to complete log playback. Check to make sure the correct
    sim-time is reached.
1. Regression Test: Old & new file format
    1. case: Record a box moving a predefined distance using both the old
    and new file formats. Check that the new file format size <= current
    file format size, and that on playback the box ends in the correct
    location. Also check the output of `gz log` is correct for both file
    formats.
    1. case: Repeat case 1 with the pioneer2dx.
    1. case: Repeat case 1 with a pendulum.
1. GUI Test: Load log file
    1. case: On log file load, the playback widget should appear, and the
    playback time set to the first sim-time value in the log file.
    1. case: An warning message should appear when a log file could not be
    opened due to improper permissions or invalid file. 
1. GUI Test: Play log file
    In all cases, the validity of a log message is based on both its
    presence and its data.
    1. case: After loading a log file, and pressing play, the client should
    receive log info messages from the server. Check that the messages
    appear, and are correct.
    1. case: When in the play mode, pressing stop should terminate the log
    info messages. Check that the messages stop
    1. case: Pressing skip backward should cause the first log info message
    to be sent.
    1. case: Pressing skip forward should cause the last log info message to
    be sent.
    1. case: When not at the end, stepping forward should produce one log
    info message.  1. case: When at the end, the step forward button should
    be disabled.  1. case: When not at the beginning, stepping backward
    should produce one log info message.
    1. case: When at the beginning, the step backward button should be disabled.
1. GUI Test: Slider functionality
    1. case: The slider should start at the zero position when log file is
    loaded.
    1. case: Moving the slider to the end should produce only the
    last log info message.
    1. case: Placing the control markers and enabling the loop feature
    should cause log info messages to repeat.
    1. case: Check that the zoom feature causes the slider to scale.
