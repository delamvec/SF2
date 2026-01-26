/*********************************************************************
 * date        : 2007.02.24
 * file        : blend_item.h
 * author      : mhh
 * description :
 */

#ifndef _blend_item_h_
#define _blend_item_h_

#define	MAX_BLEND_ITEM_VALUE		5

// Energy Crystal System - item vnum
#define ECS_ITEM_VNUM				51002

bool	Blend_Item_init();
bool	Blend_Item_load(char *file);
bool	Blend_Item_set_value(LPITEM item);
bool	Blend_Item_find(DWORD item_vnum);

// Energy Crystal System - get random bonus (for use when item is clicked)
bool	ECS_get_random_bonus(int* apply_type, int* apply_value, int* apply_duration);

#endif	/* _blend_item_h_ */
