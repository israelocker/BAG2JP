#pragma once
/* JP system/007.dbi: guarded cursor bounds and rand()%15 for extra Heat, Strike and Gas-O entries. */
typedef struct { uint32_t addr, stock, expanded; } CsStagePatch;
static const CsStagePatch cs_stage_patches[] = {
    {0x8009121Cu, 0x2412000Cu, 0x2412000Fu},
    {0x80091268u, 0x2842000Du, 0x28420010u},
    {0x800912D0u, 0x2842000Du, 0x28420010u},
    {0x80091368u, 0x2842000Du, 0x28420010u},
    {0x800913D0u, 0x2842000Du, 0x28420010u},
    {0x80091534u, 0x2842000Du, 0x28420010u},
    {0x80091554u, 0x2402000Cu, 0x2402000Fu},
    {0x80091594u, 0x2408000Cu, 0x2408000Fu},
    {0x800915ACu, 0x2842000Du, 0x28420010u},
    {0x80091658u, 0x2842000Du, 0x28420010u},
    {0x80091678u, 0x2402000Cu, 0x2402000Fu},
    {0x800916B8u, 0x2408000Cu, 0x2408000Fu},
    {0x800916D0u, 0x2842000Du, 0x28420010u},
    {0x80091744u, 0x2402000Cu, 0x2402000Fu},
    {0x8009177Cu, 0x3C032AAAu, 0x3C034444u},
    {0x80091780u, 0x3463AAABu, 0x34634445u},
    {0x80091790u, 0x00092043u, 0x00092083u},
    {0x80091794u, 0x00832023u, 0x00041900u},
    {0x80091798u, 0x00041840u, 0x00641823u},
    {0x8009179Cu, 0x00641821u, 0x00000000u},
    {0x800917A0u, 0x00031880u, 0x00000000u},
    {0x800917E8u, 0x2403000Cu, 0x2403000Fu},
    {0x80091914u, 0x2402000Cu, 0x2402000Fu},
};
static const uint8_t cs_stage_order_stock[16] = {0,2,5,1,10,7,3,8,4,9,11,6,0,0,0,0};
static const uint8_t cs_stage_order_expanded[16] = {0,0,2,5,1,1,10,7,3,8,4,9,9,11,6,0};
static const uint8_t cs_stage_inverse_stock[16] = {0,3,1,6,8,2,11,5,7,9,4,10,12,0,0,0};
static const uint8_t cs_stage_inverse_expanded[16] = {0,4,2,8,10,3,14,7,9,11,6,13,15,0,0,0};
