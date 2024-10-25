#include "mem/cache/replacement_policies/sim_object_unit_tester.hh"

#include <iostream>

#include "base/trace.hh"
#include "mem/cache/replacement_policies/fifo_rp.hh"
#include "mem/cache/replacement_policies/replaceable_entry.hh"

namespace gem5
{
namespace replacement_policy
{

SimObjectUnitTester::SimObjectUnitTester(
  const SimObjectUnitTesterParams& params):
  SimObject(params),
  nextEvent([this](){ processNextEvent(); }, name() + "nextEvent"),
  replacement_policy(params.replacement_policy),
  numEntries(params.num_entries)
{}

void
SimObjectUnitTester::processNextEvent()
{
  std::cout << "tick: " << curTick() <<
  ", Hello from SimObjectUnitTester::processNextEvent!" << std::endl;

  // create a new entry and put it in candidates
  ReplaceableEntry* temp = new ReplaceableEntry();
  temp->replacementData = replacement_policy->instantiateEntry();
  replacement_policy->reset(temp->replacementData); // record insertion tick
  // std::cout<< "Inserted tick: " <<
  //std::static_pointer_cast<FIFO::FIFOReplData>(temp->replacementData)
  //->tickInserted <<std::endl;
  candidates.push_back(temp);

  if (numEntries > 0){
    schedule(nextEvent, curTick() + 500);
    numEntries--;
  }
  else {
    // FIFO* tmp;
    bool correct = checkCorrectness(/*tmp*/);
    // free memory
    for (const auto& candidate : candidates) {
      delete candidate;
    }
    if (correct){
      exit(0);
    }
    exit(1);
  }
}

bool
SimObjectUnitTester::checkCorrectness(/*FIFO* */){
  ReplaceableEntry* victim = replacement_policy->getVictim(candidates);
  if (std::static_pointer_cast<FIFO::FIFOReplData>(
    victim ->replacementData)->tickInserted != 1){

    std::cout<<"tick: "<<std::static_pointer_cast<FIFO::FIFOReplData>(
      victim ->replacementData)->tickInserted <<std::endl;
    return false;
  }
  return true;
}

  // template <>
  // bool
  // SimObjectUnitTester::checkCorrectness<FIFO>(){
  //   ReplaceableEntry* victim = replacement_policy->getVictim(candidates);
  //   if (std::static_pointer_cast<FIFO::FIFOReplData>(victim
  //->replacementData)->tickInserted != 1){
  //     std::cout<<"tick: "<<std::static_pointer_cast<FIFO::FIFOReplData>
  //(victim ->replacementData)->tickInserted <<std::endl;
  //     return false;
  //   }
  //   return true;
  // }

  // template <>
  // bool
  // SimObjectUnitTester::checkCorrectness<Base>(){
  //   return false;
  // }


void
SimObjectUnitTester::startup()
{
  panic_if(curTick() != 0, "startup() called at a tick other than 0");
  panic_if(nextEvent.scheduled(),
  "nextEvent scheduled before startup() called! ");
  schedule(nextEvent, curTick() + 500);
}

} //namespace replacement_policy

} // namespace gem5
