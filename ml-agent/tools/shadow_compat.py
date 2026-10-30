"""Explicit, provenance-recorded adapter for an unpriced-animal overflow-helper error.
No policy source or weights are edited; all unrelated exceptions propagate.
"""
import copy
from collections import Counter


def overflow_guard(original,animals,events):
    def guarded(obs,action,info=None,*args,**kwargs):
        before=copy.deepcopy(action)
        try:
            return original(obs,action,info,*args,**kwargs)
        except KeyError as error:
            trace=error.__traceback__
            while trace.tb_next:trace=trace.tb_next
            frame=trace.tb_frame
            item=frame.f_locals.get('item')
            inventory=frame.f_locals.get('minv')
            if (frame.f_code is not original.__code__ or item not in animals
                    or error.args!=(item,) or not isinstance(inventory,dict) or item in inventory):
                raise
            # Keep the model/decoder action. Do not invent a sale price for an animal.
            action.clear();action.update(copy.deepcopy(before))
            events.append({'step':int(obs['day'])*24+int(obs['hour']),
                'helper':'night_room_value','error':f"KeyError: {item!r}",'animal':item,
                'source_file':frame.f_code.co_filename,'source_line':trace.tb_lineno,
                'overflow_items':dict(Counter(frame.f_locals.get('lost',[]))),
                'teacher_pre_helper_action':before,'returned_action':copy.deepcopy(action),
                'our_action':'skip optional overflow sales adjustment; preserve teacher pre-helper action',
                'added_market_orders':[],'changed_unit_commands':False})
            return 0
    return guarded
