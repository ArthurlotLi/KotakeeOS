/*
  Enums to keep constant with client logic. 
*/

// Actions enum - Should be kept constant between this and client 
// application logic. Each arduino will contain an array of 
// implemented actions, and within a room, no duplicate actions
// will be present (allowing deliniation between multiple lighting
// modules, for example)
const actions = {
  LIGHTING1: 50,
  LIGHTING2: 51,
  LIGHTING3: 52,
  LIGHTING4: 53,
  LIGHTING5: 54,
  CURTAINS1: 150,
  CURTAINS2: 151,
  CURTAINS3: 152,
  CURTAINS4: 153,
  CURTAINS5: 154,
  REMOTE1: 250,
  REMOTE2: 251,
  REMOTE3: 252,
  REMOTE4: 253,
  REMOTE5: 254,
  REMOTE6: 255,
  REMOTE7: 256,
  REMOTE8: 257,
  REMOTE9: 258,
  REMOTE10: 259,
  REMOTE11: 260,
  REMOTE12: 261,
  REMOTE13: 262,
  REMOTE14: 263,
  REMOTE15: 264,
  REMOTE16: 265,
  REMOTE17: 266,
  REMOTE18: 267,
  REMOTE19: 268,
  REMOTE20: 269,
  SWITCH1: 350,
  SWITCH2: 351,
  SWITCH3: 352,
  SWITCH4: 353,
  SWITCH5: 354,
  KNOB1: 450,
  KNOB2: 451,
  KNOB3: 452,
  KNOB4: 453,
  KNOB5: 454,
  // These get handled rather differently from other actions.
  // (toState represents different pre-programmed modes.)
  LEDSTRIP1: 1000,
  LEDSTRIP2: 1001,
  LEDSTRIP3: 1002,
  LEDSTRIP4: 1003,
  LEDSTRIP5: 1004,
  LEDSTRIP6: 1005,
  LEDSTRIP7: 1006,
  LEDSTRIP8: 1007,
  LEDSTRIP9: 1008,
  LEDSTRIP10: 1009,
  // Input enums. Are considered "actions" but are treated entirely differently. 
  // Seperated from actions by 5000. Do not need to be known by client.
  MOTION1: 5050,
  MOTION2: 5051,
  MOTION3: 5052,
  MOTION4: 5053,
  MOTION5: 5054,
  DOOR1: 5150,
  DOOR2: 5151,
  DOOR3: 5152,
  DOOR4: 5153,
  DOOR5: 5154,
  TEMP1: 5250,
  TEMP2: 5251,
  TEMP3: 5252,
  TEMP4: 5253,
  TEMP5: 5254,
  ADMIN1: 5350, // Not meant to be connected to anything physical. For interactions between clients and webserver.
  ADMIN2: 5351,
  ADMIN3: 5352,
  ADMIN4: 5353,
  ADMIN5: 5354,
}

// Bedroom IDs - Should be kept constant betweeen this and client
// application logic. 
const rooms = {
  BEDROOM: 1,
  LIVINGROOM: 2,
  BATHROOM: 3,
}

// End enums