/*
 * Copyright (c) 2013 ARM Limited
 * All rights reserved
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder.  You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Copyright (c) 2020 Inria
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/**
 * @file This file describes the base components used for the probe system.
 * There are currently 3 components:
 *
 * ProbePoint:          an event probe point i.e. sends a notify from the
 *                      point at which an instruction was committed.
 *
 * ProbeListener:       a listener provides a notify method that is called when
 *                      a probe point event occurs. Multiple ProbeListeners
 *                      can be added to each ProbePoint.
 *
 * ProbeListenerObject: a wrapper around a SimObject that can connect to
 *                      another SimObject on which it will add ProbeListeners.
 *
 * ProbeManager:        used to match up ProbeListeners and ProbePoints.
 *                      At <b>simulation init</b> this is handled by
 *                      regProbePoints followed by regProbeListeners being
 *                      called on each SimObject in hierarchical ordering.
 *                      ProbeListeners can be added/removed dynamically at
 *                      runtime.
 */

#ifndef __SIM_PROBE_PROBE_HH__
#define __SIM_PROBE_PROBE_HH__

#include <string>
#include <vector>

#include "base/compiler.hh"
#include "base/named.hh"
#include "base/trace.hh"
#include "debug/ProbeVerbose.hh"
#include "sim/sim_object.hh"

namespace gem5
{

/** Forward declare the ProbeManager. */
class ProbeManager;
class ProbeListener;
struct ProbeListenerObjectParams;

/**
 * Name space containing shared probe point declarations.
 *
 * Probe types that are shared between multiple types of SimObjects
 * should live in this name space. This makes it possible to use a
 * common instrumentation interface for devices such as PMUs that have
 * different implementations in different ISAs.
 */
GEM5_DEPRECATED_NAMESPACE(ProbePoints, probing);
namespace probing
{
/* Note: This is only here for documentation purposes, new probe
 * points should normally be declared in their own header files. See
 * for example pmu.hh.
 */
}

/**
 * This class is a minimal wrapper around SimObject. It is used to declare
 * a python derived object that can be added as a ProbeListener to any other
 * SimObject.
 *
 * It instantiates manager from a call to Parent.any.
 * The vector of listeners is used simply to hold onto listeners until the
 * ProbeListenerObject is destroyed.
 */
class ProbeListenerObject : public SimObject
{
  protected:
    ProbeManager *manager;
    std::vector<ProbeListener *> listeners;

  public:
    ProbeListenerObject(const ProbeListenerObjectParams &params);
    virtual ~ProbeListenerObject();
    ProbeManager* getProbeManager() { return manager; }
};

/**
 * ProbeListener base class; here to simplify things like containers
 * containing multiple types of ProbeListener.
 *
 * Note a ProbeListener is added to the ProbePoint in constructor by
 * using the ProbeManager passed in.
 */
class ProbeListener
{
  public:
    ProbeListener(ProbeManager *manager, const std::string &name);
    virtual ~ProbeListener();
    ProbeListener(const ProbeListener& other) = delete;
    ProbeListener& operator=(const ProbeListener& other) = delete;
    ProbeListener(ProbeListener&& other) noexcept = delete;
    ProbeListener& operator=(ProbeListener&& other) noexcept = delete;


    /** Allow this probe to receive notifications. */
    void enable() { _enabled = true; }

    /** Disallow this probe to receive notifications. */
    void disable() { _enabled = false; }

    /**
     * Whether this listener is allowed to receive notifications.
     *
     * @return True if this listener can process notifications.
     */
    bool enabled() const { return _enabled; }

  protected:
    ProbeManager *const manager;
    const std::string name;

  private:
    /** Whether this listener processes notifications. */
    bool _enabled;
};

/**
 * ProbeListener base class; again used to simplify use of ProbePoints
 * in containers and used as to define interface for adding removing
 * listeners to the ProbePoint.
 */
class ProbePoint
{
  protected:
    const std::string name;
  public:
    ProbePoint(const std::string &name);
    virtual ~ProbePoint() = default;

    virtual void addListener(ProbeListener *listener) = 0;
    virtual void removeListener(ProbeListener *listener) = 0;
    std::string getName() const { return name; }
};

/**
 * ProbeManager is a conduit class that lives on each SimObject,
 *  and is used to match up probe listeners with probe points.
 */
class ProbeManager : public Named
{
  private:
    /** Vector for name look-up. */
    std::vector<std::shared_ptr<ProbePoint>> points;

  public:
    /** @param object_name Name of the object to which this manager belongs. */
    ProbeManager(const std::string &object_name) : Named(object_name) {}
    virtual ~ProbeManager() = default;

    /**
     * @brief Add a ProbeListener to the ProbePoint named by pointName.
     *        If the name doesn't resolve a ProbePoint return false.
     * @param point_name name of the ProbePoint to add the ProbeListener to.
     * @param listener the ProbeListener to add.
     * @return true if added, false otherwise.
     */
    bool addListener(std::string point_name, ProbeListener &listener);

    /**
     * @brief Remove a ProbeListener from the ProbePoint named by pointName.
     *        If the name doesn't resolve a ProbePoint return false.
     * @param point_name the name of the ProbePoint to remove the ProbeListener
     *        from.
     * @param listener the ProbeListener to remove.
     * @return true if removed, false otherwise.
     */
    bool removeListener(std::string point_name, ProbeListener &listener);

    /**
     * @brief Create and add a ProbePoint to this SimObject's ProbeManager.
     * @tparam Arg The type of the ProbePoint.
     * @param pp_name The name of the ProbePoint to create.
     * @return A pointer to the probe point, so that a cached copy can
     *         be kept to generate notifications.
     */
    template <class Arg>
    std::shared_ptr<Arg>
    addPoint(const std::string &pp_name)
    {
        DPRINTFR(ProbeVerbose, "Probes: Call to addPoint \"%s\" to %s.\n",
            pp_name, name());

        for (auto p = points.begin(); p != points.end(); ++p) {
            if ((*p)->getName() == pp_name) {
                DPRINTFR(ProbeVerbose, "Probes: Call to addPoint \"%s\" to %s "
                    "failed, already added.\n", pp_name, name());
                return std::shared_ptr<Arg>();
            }
        }
        auto point = std::make_shared<Arg>(pp_name);
        points.push_back(point);
        return point;
    }
};

/**
 * ProbeListenerArgBase is used to define the base interface to a
 * ProbeListenerArg (i.e the notify method on specific type).
 *
 * It is necessary to split this out from ProbeListenerArg, as that
 * templates off the class containing the function that notify calls.
 */
template <class Arg>
class ProbeListenerArgBase : public ProbeListener
{
  public:
    ProbeListenerArgBase(ProbeManager *pm, const std::string &name)
        : ProbeListener(pm, name)
    {}
    virtual void notify(const Arg &val) = 0;
};

/**
 * ProbeListenerArg generates a listener for the class of Arg and the
 * class type T which is the class containing the function that notify will
 * call.
 *
 * Note that the function is passed as a pointer on construction.
 */
template <class T, class Arg>
class ProbeListenerArg : public ProbeListenerArgBase<Arg>
{
  private:
    T *object;
    void (T::* function)(const Arg &);

  public:
    /**
     * @param obj the class of type Tcontaining the method to call on notify.
     * @param name the name of the ProbePoint to add this listener to.
     * @param func a pointer to the function on obj (called on notify).
     */
    ProbeListenerArg(T *obj, const std::string &name,
        void (T::* func)(const Arg &))
        : ProbeListenerArgBase<Arg>(obj->getProbeManager(), name),
          object(obj),
          function(func)
    {}

    /**
     * @brief called when the ProbePoint calls notify. This is a shim through
     *        to the function passed during construction.
     * @param val the argument value to pass.
     */
    void notify(const Arg &val) override { (object->*function)(val); }
};

/**
 * ProbePointArg generates a point for the class of Arg. As ProbePointArgs talk
 * directly to ProbeListenerArgs of the same type, we can store the vector of
 * ProbeListeners as their Arg type (and not as base type).
 *
 * Methods are provided to addListener, removeListener and notify.
 */
template <typename Arg>
class ProbePointArg : public ProbePoint
{
    /** The attached listeners. */
    std::vector<ProbeListenerArgBase<Arg> *> listeners;

  public:
    ProbePointArg(std::string name)
        : ProbePoint(name)
    {
    }

    /**
     * Informs whether any listeners are attached to this probe. This can
     * be used to avoid performing costly tasks needed by the probe when
     * nobody is listening.
     *
     * @return Whether this probe has any listener.
     */
    bool hasListeners() const { return listeners.size() > 0; }

    /**
     * @brief adds a ProbeListener to this ProbePoints notify list.
     * @param l the ProbeListener to add to the notify list.
     */
    void
    addListener(ProbeListener *l) override
    {
        // check listener not already added
        if (std::find(listeners.begin(), listeners.end(), l) ==
            listeners.end()) {
            listeners.push_back(static_cast<ProbeListenerArgBase<Arg> *>(l));
        }
    }

    /**
     * @brief remove a ProbeListener from this ProbePoints notify list.
     * @param l the ProbeListener to remove from the notify list.
     */
    void
    removeListener(ProbeListener *l) override
    {
        listeners.erase(std::remove(listeners.begin(), listeners.end(), l),
                        listeners.end());
    }

    /**
     * @brief called at the ProbePoint call site, passes arg to each listener.
     * @param arg the argument to pass to each listener.
     */
    void
    notify(const Arg &arg)
    {
        for (auto l = listeners.begin(); l != listeners.end(); ++l) {
            if ((*l)->enabled()) {
                (*l)->notify(arg);
            }
        }
    }
};

} // namespace gem5

#endif//__SIM_PROBE_PROBE_HH__
