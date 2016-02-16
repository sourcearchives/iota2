/*=========================================================================

  Program:   iota2
  Language:  C++

  Copyright (c) CESBIO. All rights reserved.

  See LICENSE for details.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

=========================================================================*/
#include <cstddef>
#include <limits>
#include <vector>
#include <algorithm>

namespace iota2
{
template <typename PixelType>
class FeatureExtractionFunctor
{
public:
  using ValueType =   typename PixelType::ValueType;

  FeatureExtractionFunctor() = default;
  FeatureExtractionFunctor(size_t cpd, size_t ri, size_t ni, size_t si,
                           ValueType ndv, size_t nic)
    : m_ComponentsPerDate{cpd}, m_RedIndex{ri},
      m_NIRIndex{ni}, m_SWIRIndex{si}, m_NoDataValue{ndv}, 
      m_NumberOfInputComponents{nic}
  {
    m_NumberOfDates = m_NumberOfInputComponents/m_ComponentsPerDate;
    m_NumberOfOutputComponents = (m_NumberOfFeatures + 
                                  m_ComponentsPerDate)*m_NumberOfDates;
  };

  PixelType operator()(const PixelType& p)
  {
    PixelType result(m_NumberOfOutputComponents);

    if(p[0] == m_NoDataValue) return result;

    auto inVec = std::vector<ValueType>(p.GetDataPointer(), 
                                        p.GetDataPointer()+p.GetSize());
    auto outVec = std::vector<ValueType>{};
    auto inIt = inVec.cbegin();
    while(inIt != inVec.cend())
      {
      //copy the spectral bands
      std::copy(inIt, inIt+m_ComponentsPerDate, std::back_inserter(outVec));
      //copute the features
      auto red = *(inIt+m_RedIndex-1);
      auto nir = *(inIt+m_NIRIndex-1);
      auto swir = *(inIt+m_SWIRIndex-1);
      auto ndvi = (nir-red)/(nir+red+std::numeric_limits<ValueType>::epsilon());
      auto ndwi = (swir-nir)/(swir+nir+std::numeric_limits<ValueType>::epsilon());
      auto brightness = std::accumulate(inIt, inIt+m_ComponentsPerDate, 
                                        ValueType{0});
      //append the features
      outVec.emplace_back(ndvi);
      outVec.emplace_back(ndwi);
      outVec.emplace_back(brightness);
      //move to the next date
      std::advance(inIt, m_ComponentsPerDate);
      }
    for(size_t i=0; i<m_NumberOfOutputComponents; i++)
      result[i] = outVec[i];
    return result;
  }

  bool operator!=(FeatureExtractionFunctor<PixelType> f)
  {
    return m_ComponentsPerDate != f.m_ComponentsPerDate;
  }

protected:

  size_t m_ComponentsPerDate;
  size_t m_RedIndex;
  size_t m_NIRIndex;
  size_t m_SWIRIndex;
  ValueType m_NoDataValue;
  size_t m_NumberOfInputComponents;
  size_t m_NumberOfOutputComponents;
  size_t m_NumberOfDates;
  static constexpr size_t m_NumberOfFeatures = 3;
};
} // end namespace iota2

  
  
