/*
 *   BSD LICENSE
 *
 *   Copyright (C) Cavium, Inc. 2017.
 *
 *   Redistribution and use in source and binary forms, with or without
 *   modification, are permitted provided that the following conditions
 *   are met:
 *
 *     * Redistributions of source code must retain the above copyright
 *       notice, this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright
 *       notice, this list of conditions and the following disclaimer in
 *       the documentation and/or other materials provided with the
 *       distribution.
 *     * Neither the name of Cavium, Inc nor the names of its
 *       contributors may be used to endorse or promote products derived
 *       from this software without specific prior written permission.
 *
 *   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 *   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 *   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 *   A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 *   OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 *   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 *   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 *   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 *   THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 *   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 *   OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef _RTE_ARMV8_PMD_PRIVATE_H_
#define _RTE_ARMV8_PMD_PRIVATE_H_

#define CRYPTODEV_NAME_ARMV8_PMD	crypto_armv8
/**< ARMv8 Crypto PMD device name */

#define ARMV8_CRYPTO_LOG_ERR(fmt, args...) \
	RTE_LOG(ERR, CRYPTODEV, "[%s] %s() line %u: " fmt "\n",  \
			RTE_STR(CRYPTODEV_NAME_ARMV8_CRYPTO_PMD), \
			__func__, __LINE__, ## args)

#ifdef RTE_LIBRTE_ARMV8_CRYPTO_DEBUG
#define ARMV8_CRYPTO_LOG_INFO(fmt, args...) \
	RTE_LOG(INFO, CRYPTODEV, "[%s] %s() line %u: " fmt "\n", \
			RTE_STR(CRYPTODEV_NAME_ARMV8_CRYPTO_PMD), \
			__func__, __LINE__, ## args)

#define ARMV8_CRYPTO_LOG_DBG(fmt, args...) \
	RTE_LOG(DEBUG, CRYPTODEV, "[%s] %s() line %u: " fmt "\n", \
			RTE_STR(CRYPTODEV_NAME_ARMV8_CRYPTO_PMD), \
			__func__, __LINE__, ## args)

#define ARMV8_CRYPTO_ASSERT(con)				\
do {								\
	if (!(con)) {						\
		rte_panic("%s(): "				\
		    con "condition failed, line %u", __func__);	\
	}							\
} while (0)

#else
#define ARMV8_CRYPTO_LOG_INFO(fmt, args...)
#define ARMV8_CRYPTO_LOG_DBG(fmt, args...)
#define ARMV8_CRYPTO_ASSERT(con)
#endif

#define NBBY		8		/* Number of bits in a byte */
#define BYTE_LENGTH(x)	((x) / NBBY)	/* Number of bytes in x (round down) */

/** ARMv8 operation order mode enumerator */
enum armv8_crypto_chain_order {
	ARMV8_CRYPTO_CHAIN_CIPHER_AUTH,
	ARMV8_CRYPTO_CHAIN_AUTH_CIPHER,
	ARMV8_CRYPTO_CHAIN_NOT_SUPPORTED,
	ARMV8_CRYPTO_CHAIN_LIST_END = ARMV8_CRYPTO_CHAIN_NOT_SUPPORTED
};

/** ARMv8 cipher operation enumerator */
enum armv8_crypto_cipher_operation {
	ARMV8_CRYPTO_CIPHER_OP_ENCRYPT = RTE_CRYPTO_CIPHER_OP_ENCRYPT,
	ARMV8_CRYPTO_CIPHER_OP_DECRYPT = RTE_CRYPTO_CIPHER_OP_DECRYPT,
	ARMV8_CRYPTO_CIPHER_OP_NOT_SUPPORTED,
	ARMV8_CRYPTO_CIPHER_OP_LIST_END = ARMV8_CRYPTO_CIPHER_OP_NOT_SUPPORTED
};

enum armv8_crypto_cipher_keylen {
	ARMV8_CRYPTO_CIPHER_KEYLEN_128,
	ARMV8_CRYPTO_CIPHER_KEYLEN_192,
	ARMV8_CRYPTO_CIPHER_KEYLEN_256,
	ARMV8_CRYPTO_CIPHER_KEYLEN_NOT_SUPPORTED,
	ARMV8_CRYPTO_CIPHER_KEYLEN_LIST_END =
		ARMV8_CRYPTO_CIPHER_KEYLEN_NOT_SUPPORTED
};

/** ARMv8 auth mode enumerator */
enum armv8_crypto_auth_mode {
	ARMV8_CRYPTO_AUTH_AS_AUTH,
	ARMV8_CRYPTO_AUTH_AS_HMAC,
	ARMV8_CRYPTO_AUTH_AS_CIPHER,
	ARMV8_CRYPTO_AUTH_NOT_SUPPORTED,
	ARMV8_CRYPTO_AUTH_LIST_END = ARMV8_CRYPTO_AUTH_NOT_SUPPORTED
};

#define CRYPTO_ORDER_MAX		ARMV8_CRYPTO_CHAIN_LIST_END
#define CRYPTO_CIPHER_OP_MAX		ARMV8_CRYPTO_CIPHER_OP_LIST_END
#define CRYPTO_CIPHER_KEYLEN_MAX	ARMV8_CRYPTO_CIPHER_KEYLEN_LIST_END
#define CRYPTO_CIPHER_MAX		RTE_CRYPTO_CIPHER_LIST_END
#define CRYPTO_AUTH_MAX			RTE_CRYPTO_AUTH_LIST_END

#define HMAC_IPAD_VALUE			(0x36)
#define HMAC_OPAD_VALUE			(0x5C)

#define SHA256_AUTH_KEY_LENGTH		(BYTE_LENGTH(256))
#define SHA256_BLOCK_SIZE		(BYTE_LENGTH(512))

#define SHA1_AUTH_KEY_LENGTH		(BYTE_LENGTH(160))
#define SHA1_BLOCK_SIZE			(BYTE_LENGTH(512))

#define SHA_AUTH_KEY_MAX		SHA256_AUTH_KEY_LENGTH
#define SHA_BLOCK_MAX			SHA256_BLOCK_SIZE

typedef int (*crypto_func_t)(uint8_t *, uint8_t *, uint64_t,
				uint8_t *, uint8_t *, uint64_t,
				crypto_arg_t *);

typedef void (*crypto_key_sched_t)(uint8_t *, const uint8_t *);

/** private data structure for each ARMv8 crypto device */
struct armv8_crypto_private {
	unsigned int max_nb_qpairs;
	/**< Max number of queue pairs */
	unsigned int max_nb_sessions;
	/**< Max number of sessions */
};

/** ARMv8 crypto queue pair */
struct armv8_crypto_qp {
	uint16_t id;
	/**< Queue Pair Identifier */
	struct rte_ring *processed_ops;
	/**< Ring for placing process packets */
	struct rte_mempool *sess_mp;
	/**< Session Mempool */
	struct rte_cryptodev_stats stats;
	/**< Queue pair statistics */
	char name[RTE_CRYPTODEV_NAME_LEN];
	/**< Unique Queue Pair Name */
} __rte_cache_aligned;

/** ARMv8 crypto private session structure */
struct armv8_crypto_session {
	enum armv8_crypto_chain_order chain_order;
	/**< chain order mode */
	crypto_func_t crypto_func;
	/**< cryptographic function to use for this session */

	/** Cipher Parameters */
	struct {
		enum rte_crypto_cipher_operation direction;
		/**< cipher operation direction */
		enum rte_crypto_cipher_algorithm algo;
		/**< cipher algorithm */
		struct {
			uint16_t length;
			uint16_t offset;
		} iv;
		/**< IV parameters */

		struct {
			uint8_t data[256];
			/**< key data */
			size_t length;
			/**< key length in bytes */
		} key;

		crypto_key_sched_t key_sched;
		/**< Key schedule function */
	} cipher;

	/** Authentication Parameters */
	struct {
		enum rte_crypto_auth_operation operation;
		/**< auth operation generate or verify */
		enum armv8_crypto_auth_mode mode;
		/**< auth operation mode */

		union {
			struct {
				/* Add data if needed */
			} auth;

			struct {
				uint8_t i_key_pad[SHA_BLOCK_MAX]
							__rte_cache_aligned;
				/**< inner pad (max supported block length) */
				uint8_t o_key_pad[SHA_BLOCK_MAX]
							__rte_cache_aligned;
				/**< outer pad (max supported block length) */
				uint8_t key[SHA_BLOCK_MAX];
				/**< HMAC key (max supported block length)*/
			} hmac;
		};
		uint16_t digest_length;
		/* Digest length */
	} auth;

} __rte_cache_aligned;

/** Set and validate ARMv8 crypto session parameters */
extern int armv8_crypto_set_session_parameters(
		struct armv8_crypto_session *sess,
		const struct rte_crypto_sym_xform *xform);

/** device specific operations function pointer structure */
extern struct rte_cryptodev_ops *rte_armv8_crypto_pmd_ops;

#endif /* _RTE_ARMV8_PMD_PRIVATE_H_ */
