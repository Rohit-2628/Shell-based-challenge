# Latveria Breach

## Premise
You have established initial access to a fortified perimeter station within the Latverian government network. Intelligence reports indicate a classified state archive vault is hosted on this node.

However, perimeter defenses are on high alert. If defensive traps are triggered, a containment protocol will activate with a countdown timer. You must navigate the node, locate intelligence transmissions, unlock the state archive vault, escalate privileges to root, and disarm any active defense grid using the sovereign override flag.

## Connection Information
- **Protocol**: SSH
- **Host**: Target Instance (`127.0.0.1` locally)
- **Port**: `2229`
- **Username**: `intruder`
- **Password**: `doom_is_master`

```bash
ssh -p 2229 intruder@<target-host>
```

## Objective
1. Inspect the host and identify ongoing system activities and transmissions.
2. Access the classified vault (`~/vault`).
3. If defensive mechanisms are tripped, escalate privileges to root to secure the override key.
4. Execute the override disarm protocol (`~/abort_destruct`) to survive and obtain the final flag.
