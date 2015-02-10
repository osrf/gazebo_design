## API for Gazebo Physics Preset Profiles
***Gazebo Design Document***

### Overview
Currently, Gazebo only supports one `<physics>` in SDF.. Furthermore, if a user desires to change simulation properties after the world file is loaded, they must write a plugin to change physics engine parameters individually via the physics API. If a user has multiple physics profiles in mind for a world--for example, one tuned for performance and the other tuned for accuracy--the current method for switching between them is clunky and verbose.

This design document proposes a small change to SDF to support multiple physics blocks in SDF, as well as an API to manage switching between these preset physics profiles.

### Requirements
Via world file SDF, the user must be able to specify:

- Multiple physics blocks for different physics engines, with different simulation properties, etc.

- The name of a particular physics block.

- The name of the default physics block for a particular world.

While Gazebo is running, a developer can use the API to do the following:

- Switch between the different physics profiles specified in SDF. Switching to a new profile must affect changes to the physics engine.

- Read the name and parameters of any profile known to the simulation.

- Read the name and parameters of the current profile.

- Create a new profile and specify physics parameters programmatically.

- Save a new profile to SDF.

- Load a new profile from SDF.

### Architecture
The new SDF architecture includes `name` attribute for the `physics` element. Another `physics` attribute, `default`, is a boolean value that is true if this physics block is the default profile for the world. The default value of `default` is `false`. If multiple `physics` elements have `default` set to `true`, then the first one marked as default is chosen as the default, with a warning to the user. If no `physics` elements have `default` set to `true`, then the first physics element is chosen.

~~~
<sdf version="1.5">
  <world name="default">
    ...
    <physics name="preset1">
      <iterations>1000</iterations>
      ...
    </physics>
    <physics name="preset2" default="true">
      <iterations>100</iterations>
      ...
    </physics>
    ...
  </world>
</sdf>
~~~

During runtime, the physics profiles will be managed by a new physics class, `PresetManager`. `PresetManager` is the interface between the physics engine and the user (via SDF or programmatic commands). It is instantiated shortly after the construction of the `PhysicsEngine` object, in `World::Load`. `World` stores a pointer to its `PresetManager` class.

`PresetManager` parses the world SDF and collects all of the physics blocks in a map for easy and fast access. Its data members will include a map structure to store all known preset profiles and a pointer to the `PhysicsEngine` for its world.

For the sake of cleaner code, a `Preset` class will also be introduced. This abstraction helps reduce the complexity of managing individual physics profiles. However, the `Preset` class is not visible to the user, since the `PresetManager` interface should be adequate for their purposes. `Preset` is merely an internal convenience for `PresetManager`.

`PresetManager` provides an interface for loading and saving physics profiles as SDF. However, the process of choosing, opening, and reading/writing a file is up to the user. Thus, `PresetManager` receives `sdf::Element` pointers as input, stores them, modifies them, and outputs them to the user. The user decides where the load the SDF from and how to save it (insert it into an existing world file, create a new world file, etc.).

### Interfaces

The C++ interface is as follows:

~~~
class Preset
{
  public: std::string Name() const;
  public: boost::any _value Param(const std::string& _key) const;
  public: void Param(const std::string& _key, boost::any _value);
  public: sdf::ElementPtr SDF() const;
  public: void SDF(sdf::ElementPtr _sdfElement);
}

class PresetManager
{
  public: bool CurrentProfile(const std::string& _name);

  public: std::string CurrentProfile() const;

  public: std::vector<std::string> AllProfiles() const;

  public: bool ProfileParam(const std::string& _profileName,
                               const std::string& _key,
                               const boost::any &_value);

  public: boost::any ProfileParam(const std::string &_name) const;

  public: bool CurrentProfileParam(const std::string& _key,
                                      const boost::any &_value);

  public: void CreateProfile(const std::string& _name);

  public: std::string CreateProfile(sdf::ElementPtr _sdf);

  public: void RemoveProfile(const std::string& _name);

  public: sdf::ElementPtr ProfileSDF(const std::string &_name) const;

  public: void ProfileSDF(const std::string &_name,
              sdf::ElementPtr _sdf);
};
~~~

The command line interface allows the user to change between profiles quickly during runtime without interacting with a GUI or writing a plugin, or specify a profile besides the default on startup.

To specify a profile on starting gzserver (or gazebo):

~~~
gzserver -o [ --profile ] arg
~~~

where `arg` is the name of a profile in the world file.

To change the profile during runtime:

~~~
gz physics --profile arg
~~~

where `arg` is the name of a profile in the current `PresetManager`.

### Tests
Physics Presets Integration Test (each sub-item represents one test case):

  - Initialize a world with several preset blocks. Expect that `PhysicsEngine` reports the default physics parameters.

  - Set one parameter using `CurrentProfileParam`. Expect that this parameter and only this parameter changed in `PhysicsEngine`.

  - Switch to a different preset profile using `PresetManager::CurrentProfile`. Expect `PhysicsEngine` reports different physics parameters.

  - Create a new profile from SDF using `CreateProfile(sdf::ElementPtr)`. Switch to the new profile. Expect that `PhysicsEngine` reports the new physics parameters.

  - Initialize a world with a legacy `<world>` and `<physics>` blocks without `default` or `name` attributes. The world should assign a default name to a profile based on the given physics parameters, and set it as current profile.

### Pull Requests
This implementation will require one pull request to sdformat and at least one pull request to gazebo.

### Future Work
My hope is that this API can be followed by a graphical tool for loading, tuning and saving preset physics profiles. Imagine loading Atlas with the default parameters, watching it fall down, then using GUI sliders to change physics parameters while restarting and re-running the standing or walking controllers until the robot stands, and finally saving the profile with a new name--all without restarting Gazebo. However, the design for this tool can wait until after a first pass at the design and implementation of the API.
