import matplotlib.pyplot as plt

cycles=[]
cmr=[]

with open("dataset.txt") as f:
    for line in f:
        parts=line.split()
        cycles.append(float(parts[3])/1e9)
        cmr.append(float(parts[2]))

plt.scatter(cycles, cmr)
plt.xlabel("CPU Cycles (Billions)")
plt.ylabel("Cache Miss Rate (%)")
plt.title("Execution Cost vs Cache Disturbance")
plt.savefig("cycles.png", dpi=300)
print("Graph saved as ipc_cache.png")
