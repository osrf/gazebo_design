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
The new SDF architecture will include a new attribute under the `world` element, `name`. The `physics` element will also have a new `name` attribute.

```
<sdf>
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
```

The 

### Interfaces

```
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

  public: bool SetCurrentProfileParam(const std::string& _key,
                                      const boost::any &_value);

  public: void CreateProfile(const std::string& _name);

  public: std::string CreateProfile(sdf::ElementPtr _sdf);

  public: void RemoveProfile(const std::string& _name);

  public: sdf::ElementPtr GetProfileSDF(const std::string &_name) const;

  public: void SetProfileSDF(const std::string &_name,
              sdf::ElementPtr _sdf);
};
```

### Tests


### Pull Requests
This implementation will require one pull request to sdformat and at least one pull request to gazebo.

### Future Work
My hope is that this API can be followed by a graphical tool for loading, tuning and saving preset physics profiles. Imagine loading Atlas with the default parameters, watching it fall down, then using GUI sliders to change physics parameters while restarting and re-running the standing or walking controllers until the robot stands, and finally saving the profile with a new name--all without restarting Gazebo. However, the design for this tool can wait until the design for the API has been finalized.
