## Battery and power flow design ideas

1. Timer for constant rate of power consumption

    A simple approach to modeling energy consumption is to assume a constant rate
    of power consumption and limit the time of operation.
    If a system is not in use, there should be a way for it to be disabled
    to stop the time and then re-enable it to start the timer again.

2. Energy flows within a single model

    The rate of power consumption in a system often varies.
    For example the power consumption of a wheeled robot depends on
    its driving speed and whether it is driving uphill, downhill, or on flat ground.
	So a more detailed model of power consumption would involve computing power
	consumption of individual motors and sensors over short time increments
	and subtracting the energy consumption from the stored energy in the battery.
	If this is implemented as a `ModelPlugin`, it should be straightforward to
	keep track of energy flows within the model, using the C++ API.

3. Energy flows between models

    In order to allow a large robot to recharge the batteries of a smaller robot
	or for a robot to connect to a charging station, energy needs to flow
	between different models.
	If energy is tracked using a `ModelPlugin`, ignition transport should be
	used to communicate the energy flow information between models, since it
	is difficult to use the C++ API between plugins.