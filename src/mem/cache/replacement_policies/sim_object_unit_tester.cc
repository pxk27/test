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
  replacementPolicy(params.replacement_policy),
  numEntries(params.num_entries),
  replacementPolicyName(params.name)
{}

void
SimObjectUnitTester::processNextEvent()
{
  std::cout << "tick: " << curTick() <<
  ", Hello from SimObjectUnitTester::processNextEvent!" << std::endl;

  // create a new entry and put it in candidates
  ReplaceableEntry* temp = new ReplaceableEntry();
  temp->replacementData = replacementPolicy->instantiateEntry();
  replacementPolicy->reset(temp->replacementData); // record insertion tick
  // std::cout<< "Inserted tick: " <<
  //std::static_pointer_cast<FIFO::FIFOReplData>(temp->replacementData)
  //->tickInserted <<std::endl;
  candidates.push_back(temp);

  if (numEntries > 0){
    schedule(nextEvent, curTick() + 500);
    numEntries--;
  }
  else {
    bool correct = checkCorrectness(replacementPolicy);
    // free memory
    freeCandidates();
    if (correct){
      exit(0);
    }
    exit(1);
  }
}

void
SimObjectUnitTester::freeCandidates(void){
  for (const auto& candidate : candidates) {
    delete candidate;
  }
}

// bool
// SimObjectUnitTester::checkCorrectness(void){
//   return false;
// }


bool
SimObjectUnitTester::checkCorrectness(FIFO*){
// SimObjectUnitTester::checkCorrectnessFIFO(){

  ReplaceableEntry* victim = replacementPolicy->getVictim(candidates);
  if (std::static_pointer_cast<FIFO::FIFOReplData>(
    victim ->replacementData)->tickInserted != 1){

    std::cout<<"tick: "<<std::static_pointer_cast<FIFO::FIFOReplData>(
      victim ->replacementData)->tickInserted <<std::endl;
    return false;
  }
  return true;
}

bool
SimObjectUnitTester::checkCorrectness(LRU*){

// SimObjectUnitTester::checkCorrectnessLRU(){
  // touch the first entry. This way, the second entry to be instantiated will
  // be evicted.
  replacementPolicy->touch(candidates[0]->replacementData);
  ReplaceableEntry* victim = replacementPolicy->getVictim(candidates);
  Tick evictedLastTick = std::static_pointer_cast<LRU::LRUReplData>(
    victim->replacementData)->lastTouchTick;
  Tick expectedEvictedLastTick = std::static_pointer_cast<LRU::LRUReplData>(
    candidates[1]->replacementData)->lastTouchTick;
  // for (const auto& candidate : candidates){
  //   if (std::static_pointer_cast<LRU::LRUReplData>(
  //     candidate->replacementData)->lastTouchTick > evictedLastTick){
  //     return false;
  //   }
  // }
  if (evictedLastTick != expectedEvictedLastTick){
    return false;
  }
  return true;
}



bool
SimObjectUnitTester::checkCorrectness(Base*){
  // std::cout<<"Something has gone wrong!"<<std::endl;

  // return false;
  if (replacementPolicyName== "FIFO"){
    // return checkCorrectnessFIFO();
    std::cout<<"Calling checkCorrectness for FIFO"<<std::endl;
    FIFO* tmp = nullptr;
    return checkCorrectness(tmp);
  }
  else if (replacementPolicyName =="LRU"){
    std::cout<<"Calling checkCorrectness for LRU"<<std::endl;
    LRU* tmp = nullptr;
    return checkCorrectness(tmp);
  } else{
    std::cout<< "Something is wrong! from base"<<std::endl;
    return false;
  }

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

// bool
// FIFOTester::checkCorrectness(){
//   ReplaceableEntry* victim = replacement_policy->getVictim(candidates);
//   if (std::static_pointer_cast<FIFO::FIFOReplData>(
//     victim ->replacementData)->tickInserted != 1){

//     std::cout<<"tick: "<<std::static_pointer_cast<FIFO::FIFOReplData>(
//       victim ->replacementData)->tickInserted <<std::endl;
//     return false;
//   }
//   return true;
// }

// bool
// LRUTester::checkCorrectness(){
//   // touch the first entry. This way, the second entry to be instantiated
//   // will be evicted.
//   replacement_policy->touch(candidates[0]->replacementData);
//   ReplaceableEntry* victim = replacement_policy->getVictim(candidates);
//   Tick evictedLastTick = std::static_pointer_cast<LRU::LRUReplData>(
//   victim->replacementData)->lastTouchTick;
//   for (const auto& candidate : candidates){
//     if (std::static_pointer_cast<LRU::LRUReplData>(
//     candidate->replacementData)->lastTouchTick > evictedLastTick){
//       return false;
//     }
//   }
//   return true;
// }




} //namespace replacement_policy

} // namespace gem5
