#ifndef __MEM_CACHE_REPLACEMENT_POLICIES_SIM_OBJECT_UNIT_TESTER_HH__
#define __MEM_CACHE_REPLACEMENT_POLICIES_SIM_OBJECT_UNIT_TESTER_HH__

#include "mem/cache/replacement_policies/base.hh"
#include "mem/cache/replacement_policies/fifo_rp.hh"
#include "mem/cache/replacement_policies/lru_rp.hh"
#include "mem/cache/replacement_policies/replaceable_entry.hh"
#include "params/SimObjectUnitTester.hh"
#include "sim/eventq.hh"
#include "sim/sim_object.hh"

// For now, focus on implementing something for the FIFO replacement policy
namespace gem5
{

namespace replacement_policy{

class SimObjectUnitTester : public SimObject
{
  private:
    EventFunctionWrapper nextEvent;
  protected:
  // the type of ReplacementCandidates is std::vector<ReplaceableEntry*>
  ReplacementCandidates candidates;
  replacement_policy::Base* replacementPolicy;
  int numEntries;
  std::string replacementPolicyName;

  void processNextEvent();

  bool checkCorrectness(FIFO*);
  bool checkCorrectness(LRU*);
  // bool checkCorrectnessFIFO();
  // bool checkCorrectnessLRU();
  bool checkCorrectness(Base*);

  // virtual bool checkCorrectness();

  void freeCandidates();

public:
  SimObjectUnitTester(const SimObjectUnitTesterParams& params);
  virtual void startup() override;
};


// class FIFOTester : public SimObjectUnitTester{
//   private:
//     virtual bool checkCorrectness() override;
// };

// class LRUTester : public SimObjectUnitTester{
//   private:
//     virtual bool checkCorrectness() override;
// };



} //namespace replacement_policy

} //namespace gem5

#endif // __SIM_OBJECT_UNIT_TESTER_SIM_OBJECT_UNIT_TESTER_HH__
