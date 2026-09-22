class NumericalSimulator:
    def euler(self,derivative,initial,dt,steps):
        values=[float(initial)]; x=float(initial)
        for i in range(steps):
            x += float(derivative(i*dt,x))*dt; values.append(x)
        return values
    def monte_carlo(self,sampler,model,iterations=1000):
        values=[float(model(sampler())) for _ in range(iterations)]
        mean=sum(values)/len(values)
        variance=sum((v-mean)**2 for v in values)/len(values)
        return {"mean":mean,"variance":variance,"samples":values}
