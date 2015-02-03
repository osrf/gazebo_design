## API for Gazebo Physics Preset Profiles
***Gazebo Design Document***

### Overview
Currently, Gazebo only supports one <physics> tag specified in SDF. Furthermore, if a user desires to change simulation properties, they must write a plugin to change physics engine parameters individually via the physics API.

This design document proposes a small change to SDF to support multiple physics blocks in SDF, as well as an API to manage switching between these preset physics profiles.

### Requirements
Via world file SDF, the user must be able to specify:

Multiple physics blocks for different physics engines, with different simulation properties, etc.

The name of a particular physics block.

The name of the default physics block for a particular world.

While Gazebo is running, a developer can use the API to do the following:

Switch between the different physics profiles specified in SDF. Switching to a new profile must affect changes to the physics engine.

Read the name and parameters of any profile known to the simulation.

Read the name and parameters of the current profile.

Create a new profile and specify physics parameters programmatically.

Save a new profile to an SDF file.

Load a new profile from an SDF file.

### Architecture
The new SDF architecture includes a new attribute under the `world` element, `name`. The `physics` element also has a new `name` attribute.

~~~
<sdf version="1.5">
  <world name="..." default_physics="preset1">
    ...
    <physics name="preset1">
      <iterations>1000</iterations>
      ...
    </physics>
    <physics name="preset2">
      <iterations>100</iterations>
      ...
    </physics>
    ...
  </world>
</sdf>
~~~

During runtime, the physics profiles will be managed by a new physics class, `PresetManager`. `PresetManager` is the interface between the physics engine and the user (via SDF or programmatic commands). It is instantiated shortly after the construction of the `PhysicsEngine` object, in `World::Load`. `World` stores a pointer to its `PresetManager` class.

`PresetManager` parses the world SDF and collects all of the physics blocks in a map for easy and fast access. Its data members will include a map structure to store all known preset profiles and a pointer to the `PhysicsEngine` for its world.

For the sake of cleaner code, a Preset class will also be introduced. This abstraction helps reduce the complexity of managing individual physics profiles. However, the Preset class is not visible to the user, since the PresetManager interface should be adequate for their purposes. Preset is merely an internal convenience for PresetManager.

PresetManager provides an interface for loading and saving physics profiles as SDF. However, the process of choosing, opening, and reading/writing a file is up to the user. Thus, PresetManager receives `sdf::Element` pointers as input, stores them, modifies them, and outputs them to the user. The user decides where the load the SDF from and how to save it (insert it into an existing world file, create a new world file, etc.).

### Interfaces

~~~
class Preset
{
  public: std::string GetName();
  public: boost::any _value GetParam(const std::string& _key);
  public: void SetParam(const std::string& _key, boost::any _value);
  public: sdf::ElementPtr GetSDF();
  public: void SetSDF(sdf::ElementPtr _sdfElement);
}

class PresetManager
{
  public: bool SetCurrentProfile(const std::string& _name);

  public: std::string GetCurrentProfile() const;

  public: std::vector<std::string> GetAllProfiles() const;

  public: bool SetProfileParam(const std::string& _profileName,
                               const std::string& _key,
                               const boost::any &_value);

  public: boost::any GetProfileParam(const std::string &_name);

  public: bool SetCurrentProfileParam(const std::string& _key,
                                      const boost::any &_value);

  public: void CreateProfile(const std::string& _name);

  public: std::string CreateProfile(sdf::ElementPtr _sdf);

  public: void RemoveProfile(const std::string& _name);

  public: sdf::ElementPtr GetProfileSDF(const std::string &_name) const;

  public: void SetProfileSDF(const std::string &_name,
              sdf::ElementPtr _sdf);
};
~~~

### Tests
1. Physics Presets Integration Test (each sub-item represents one test case):
  - Initialize a world with several preset blocks. Expect that `PhysicsEngine` reports the default physics parameters.
  - Set one parameter using `SetCurrentProfileParam`. Expect that this parameter and only this parameter changed in `PhysicsEngine`.
  - Switch to a different preset profile using `PresetManager::SetCurrentProfile`. Expect `PhysicsEngine` reports different physics parameters.
  - Create a new profile from SDF using `CreateProfile(sdf::ElementPtr)`. Switch to the new profile. Expect that `PhysicsEngine` reports the new physics parameters.

It's possible to write a unit test for `PresetManager`, but it doesn't seem particularly helpful, since so many of its operations effect the state of the physics engine.

### Pull Requests
This implementation will require one pull request to sdformat and at least one pull request to gazebo.

### Future Work
My hope is that this API can be followed by a graphical tool for loading, tuning and saving preset physics profiles. Imagine loading Atlas with the default parameters, watching it fall down, then using GUI sliders to change physics parameters while restarting and re-running the standing or walking controllers until the robot stands, and finally saving the profile with a new name--all without restarting Gazebo. However, the design for this tool can wait until after a first pass at the design and implementation of the API.
